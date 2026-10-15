"""Empirical estimation-error models learned from the real SiP dataset.

SiP (Software in Partnership Ltd, 2004-2014) contains ~10k real software tasks
with the hours *estimated before work started* and the hours *actually spent*.
Source: https://github.com/Derek-Jones/SiP_dataset (CC BY-NC-ND 4.0), described
in Jones & Cullum, "A conversation around the analysis of the SiP effort
estimation dataset" (arXiv:1901.01621). Raw files are kept unmodified in
datasets/sip/; everything below is computed from them at runtime.

What this module provides:
  * a size-bucketed actual/estimate ratio model ("how wrong are estimates of
    this size, historically") that is fitted only on data observed *before*
    the period it is evaluated on;
  * a temporal-holdout and rolling-origin benchmark comparing raw human
    estimates with the calibrated forecast on later, unseen tasks;
  * a feature-level (project breakdown) ratio pool used as the empirical
    systemic-uncertainty distribution in the Monte Carlo engine.
"""
from __future__ import annotations

import csv
import math
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from .evaluation.benchmark import PredictionRecord, evaluate_predictions

DATASET_DIR = Path(__file__).resolve().parents[3] / "datasets" / "sip"
DATASET_INFO = {
    "name": "SiP effort estimation dataset",
    "publisher": "Software in Partnership Ltd / Derek M. Jones",
    "source_url": "https://github.com/Derek-Jones/SiP_dataset",
    "source_commit": "fed32c65e974bdcabd417c695508fed05f93c215",
    "paper": "https://arxiv.org/abs/1901.01621",
    "license": "CC BY-NC-ND 4.0 (non-commercial research use; raw files redistributed unmodified)",
}

# Statuses that represent work that was actually carried out.
_DONE_STATUSES = {"FINISHED", "COMPLETED", "RELEASED", "CHRONICLE"}
# Upper edges (exclusive) of estimate-size buckets, in hours.
SIZE_BUCKET_EDGES = (4.0, 8.0, 20.0, 50.0)
MIN_BUCKET_CASES = 30
HOLDOUT_CUTOFF = date(2011, 1, 1)
AGGREGATE_MIN_ESTIMATE_HOURS = 40.0
AGGREGATE_MIN_TASKS = 5


@dataclass(frozen=True)
class SipTask:
    task_id: str
    summary: str
    category: str
    subcategory: str
    project: str
    breakdown: str
    estimate_hours: float
    actual_hours: float
    estimated_on: date


@dataclass(frozen=True)
class SipAggregate:
    """All tasks of one project breakdown code (a feature / work package)."""

    aggregate_id: str
    project: str
    n_tasks: int
    estimate_hours: float
    actual_hours: float
    first_estimated_on: date
    last_estimated_on: date

    @property
    def ratio(self) -> float:
        return self.actual_hours / self.estimate_hours


def _parse_date(raw: str) -> Optional[date]:
    try:
        return datetime.strptime(raw.strip(), "%d-%b-%y").date()
    except (ValueError, AttributeError):
        return None


@lru_cache(maxsize=4)
def load_sip_tasks(dataset_dir: Path = DATASET_DIR) -> tuple[SipTask, ...]:
    task_file = dataset_dir / "Sip-task-info.csv"
    date_file = dataset_dir / "est-act-dates.csv"
    if not task_file.exists() or not date_file.exists():
        raise FileNotFoundError(
            f"SiP dataset not found in {dataset_dir}. Run `python scripts/fetch_datasets.py`."
        )
    with open(date_file, encoding="utf-8", newline="") as f:
        estimated_on = {row["TaskNumber"]: _parse_date(row["EstimateOn"]) for row in csv.DictReader(f)}

    tasks: dict[str, SipTask] = {}
    # The file is Latin-1 encoded; one row per (task, developer). Task-level
    # HoursEstimate/HoursActual are repeated on each row, so keep the first.
    with open(task_file, encoding="latin-1", newline="") as f:
        for row in csv.DictReader(f):
            tid = row["TaskNumber"]
            if tid in tasks or row["StatusCode"] not in _DONE_STATUSES:
                continue
            try:
                est = float(row["HoursEstimate"])
                act = float(row["HoursActual"])
            except ValueError:
                continue
            when = estimated_on.get(tid)
            if est <= 0 or act <= 0 or when is None:
                continue
            tasks[tid] = SipTask(
                task_id=tid,
                summary=row["Summary"].strip(),
                category=row["Category"],
                subcategory=row["SubCategory"],
                project=row["ProjectCode"],
                breakdown=row["ProjectBreakdownCode"],
                estimate_hours=est,
                actual_hours=act,
                estimated_on=when,
            )
    return tuple(sorted(tasks.values(), key=lambda t: (t.estimated_on, int(t.task_id))))


def build_aggregates(tasks: Sequence[SipTask], development_only: bool = True) -> list[SipAggregate]:
    """Group tasks into work packages (project x breakdown code).

    By default only 'Development' tasks are used: support, meetings and
    marketing entries carry budgets rather than estimates of scoped work,
    and the app only estimates development work.
    """
    groups: dict[tuple[str, str], list[SipTask]] = defaultdict(list)
    for t in tasks:
        if development_only and t.category != "Development":
            continue
        groups[(t.project, t.breakdown)].append(t)
    aggregates = []
    for (project, breakdown), items in groups.items():
        est = sum(t.estimate_hours for t in items)
        if est < AGGREGATE_MIN_ESTIMATE_HOURS or len(items) < AGGREGATE_MIN_TASKS:
            continue
        aggregates.append(
            SipAggregate(
                aggregate_id=f"{project}/{breakdown}",
                project=project,
                n_tasks=len(items),
                estimate_hours=round(est, 2),
                actual_hours=round(sum(t.actual_hours for t in items), 2),
                first_estimated_on=min(t.estimated_on for t in items),
                last_estimated_on=max(t.estimated_on for t in items),
            )
        )
    return sorted(aggregates, key=lambda a: a.first_estimated_on)


def _bucket(estimate_hours: float) -> int:
    return bisect_right(SIZE_BUCKET_EDGES, estimate_hours)


def bucket_label(index: int) -> str:
    edges = (0.0, *SIZE_BUCKET_EDGES, math.inf)
    lo, hi = edges[index], edges[index + 1]
    return f">= {lo:g}h" if math.isinf(hi) else f"{lo:g}-{hi:g}h"


class RatioQuantileModel:
    """Predicts actual = estimate x ratio, with ratio quantiles learned per size bucket."""

    def __init__(self, ratios_by_bucket: dict[int, np.ndarray], pooled: np.ndarray):
        self.ratios_by_bucket = ratios_by_bucket
        self.pooled = pooled

    @classmethod
    def fit(cls, pairs: Sequence[tuple[float, float]]) -> "RatioQuantileModel":
        """Fit from (estimate, actual) pairs. Never pass evaluation data here."""
        if not pairs:
            raise ValueError("Cannot fit ratio model without training data")
        by_bucket: dict[int, list[float]] = defaultdict(list)
        pooled = []
        for est, act in pairs:
            r = act / est
            by_bucket[_bucket(est)].append(r)
            pooled.append(r)
        return cls(
            {b: np.sort(np.asarray(v)) for b, v in by_bucket.items()},
            np.sort(np.asarray(pooled)),
        )

    def ratios_for(self, estimate_hours: float) -> np.ndarray:
        r = self.ratios_by_bucket.get(_bucket(estimate_hours))
        return r if r is not None and len(r) >= MIN_BUCKET_CASES else self.pooled

    def predict(self, estimate_hours: float, probs: Sequence[float] = (0.1, 0.5, 0.9)) -> list[float]:
        q = np.quantile(self.ratios_for(estimate_hours), probs)
        return [float(estimate_hours * x) for x in q]


def _metrics_dict(m) -> dict:
    return {
        "n_cases": m.n_cases,
        "mae": round(m.mae, 2),
        "mdape": round(m.mdape, 2),
        "wape": round(m.wape, 2),
        "pred_25": round(m.pred_25, 2),
        "interval_coverage": round(m.interval_coverage, 2),
        "mean_interval_width": round(m.mean_interval_width, 2),
    }


def _evaluate(model: Optional[RatioQuantileModel], test: Sequence, label: str, split: str) -> dict:
    """Evaluate on tasks or aggregates. model=None means 'raw estimate, no interval'."""
    records = []
    for i, t in enumerate(test):
        case_id = getattr(t, "task_id", None) or getattr(t, "aggregate_id", str(i))
        if model is None:
            p10 = p50 = p90 = t.estimate_hours
        else:
            p10, p50, p90 = model.predict(t.estimate_hours)
        records.append(PredictionRecord(case_id, t.actual_hours, p50, p10, p90))
    out = _metrics_dict(evaluate_predictions(label, records, split=split))
    if model is None:
        # A single number has no interval; report coverage as not applicable.
        out["interval_coverage"] = None
        out["mean_interval_width"] = None
    return out


@lru_cache(maxsize=1)
def run_sip_benchmark() -> dict:
    """Temporal holdout + rolling-origin evaluation on real SiP data.

    Every model is fitted only on tasks estimated strictly before the evaluated
    period, so no future information leaks into a prediction.
    """
    tasks = load_sip_tasks()
    train = [t for t in tasks if t.estimated_on < HOLDOUT_CUTOFF]
    test = [t for t in tasks if t.estimated_on >= HOLDOUT_CUTOFF]
    model = RatioQuantileModel.fit([(t.estimate_hours, t.actual_hours) for t in train])

    holdout = {
        "train_period": f"{train[0].estimated_on.isoformat()} .. {train[-1].estimated_on.isoformat()}",
        "test_period": f"{test[0].estimated_on.isoformat()} .. {test[-1].estimated_on.isoformat()}",
        "n_train": len(train),
        "n_test": len(test),
        "baseline": _evaluate(None, test, "human-estimate", "test"),
        "calibrated": _evaluate(model, test, "parallax-empirical", "test"),
    }

    # Per-bucket view on the same holdout, to show where calibration helps or hurts.
    by_bucket = []
    for b in range(len(SIZE_BUCKET_EDGES) + 1):
        subset = [t for t in test if _bucket(t.estimate_hours) == b]
        if len(subset) < 10:
            continue
        by_bucket.append(
            {
                "bucket": bucket_label(b),
                "n_test": len(subset),
                "baseline_mae": _evaluate(None, subset, "h", "test")["mae"],
                "calibrated_mae": _evaluate(model, subset, "c", "test")["mae"],
                "calibrated_coverage": _evaluate(model, subset, "c", "test")["interval_coverage"],
                "train_ratio_p50": round(float(np.median(model.ratios_for(subset[0].estimate_hours))), 3),
            }
        )

    # Rolling origin: for each year, compare a model frozen after the first
    # year with a model re-fitted on all history available at that point.
    years = sorted({t.estimated_on.year for t in tasks})
    first_year = years[0] if sum(t.estimated_on.year == years[0] for t in tasks) >= 200 else years[1]
    frozen_train = [t for t in tasks if t.estimated_on.year <= first_year]
    frozen = RatioQuantileModel.fit([(t.estimate_hours, t.actual_hours) for t in frozen_train])
    curve = []
    for year in years:
        if year <= first_year:
            continue
        history = [t for t in tasks if t.estimated_on.year < year]
        year_tasks = [t for t in tasks if t.estimated_on.year == year]
        if len(year_tasks) < 50:
            continue
        rolling = RatioQuantileModel.fit([(t.estimate_hours, t.actual_hours) for t in history])
        base = _evaluate(None, year_tasks, "h", "test")
        fro = _evaluate(frozen, year_tasks, "f", "test")
        rol = _evaluate(rolling, year_tasks, "r", "test")
        curve.append(
            {
                "year": year,
                "n_history": len(history),
                "n_test": len(year_tasks),
                "baseline_mae": base["mae"],
                "frozen_mae": fro["mae"],
                "rolling_mae": rol["mae"],
                "baseline_pred_25": base["pred_25"],
                "rolling_pred_25": rol["pred_25"],
                "frozen_coverage": fro["interval_coverage"],
                "rolling_coverage": rol["interval_coverage"],
            }
        )

    # Feature-level (aggregate) holdout: the scale at which the app forecasts.
    aggregates = build_aggregates(tasks)
    agg_train = [a for a in aggregates if a.first_estimated_on < HOLDOUT_CUTOFF]
    agg_test = [a for a in aggregates if a.first_estimated_on >= HOLDOUT_CUTOFF]
    aggregate_section = {
        "n_aggregates": len(aggregates),
        "n_train": len(agg_train),
        "n_test": len(agg_test),
        "note": "Development tasks only. Work packages span several years; split uses the first estimate date. Small n.",
    }
    if len(agg_train) >= 10 and len(agg_test) >= 5:
        pooled = np.sort(np.asarray([a.ratio for a in agg_train]))
        agg_model = RatioQuantileModel({}, pooled)
        aggregate_section["baseline"] = _evaluate(None, agg_test, "h", "test")
        aggregate_section["calibrated"] = _evaluate(agg_model, agg_test, "c", "test")

    return {
        "dataset": {
            **DATASET_INFO,
            "n_tasks": len(tasks),
            "period": f"{tasks[0].estimated_on.isoformat()} .. {tasks[-1].estimated_on.isoformat()}",
        },
        "method": (
            "Forecast = estimate x quantiles of historical actual/estimate ratios for the same "
            "estimate-size bucket, fitted only on earlier tasks. Baseline = the human estimate as-is."
        ),
        "holdout": holdout,
        "holdout_by_bucket": by_bucket,
        "learning_curve": {"frozen_after_year": first_year, "points": curve},
        "aggregate_level": aggregate_section,
    }


@lru_cache(maxsize=1)
def systemic_ratio_pool() -> tuple[float, ...]:
    """Feature-level actual/estimate ratios, divided by their median.

    Centering removes SiP's own estimator bias, so the pool contributes only
    the empirical *spread* of feature-level error; bias is learned separately
    from this workspace's recorded actuals.
    """
    ratios = np.asarray([a.ratio for a in build_aggregates(load_sip_tasks())])
    return tuple(float(x) for x in ratios / np.median(ratios))


def dataset_summary() -> dict:
    tasks = load_sip_tasks()
    aggregates = build_aggregates(tasks)
    ratios = np.asarray([t.actual_hours / t.estimate_hours for t in tasks])
    agg_ratios = np.asarray([a.ratio for a in aggregates])
    categories: dict[tuple[str, str], list[SipTask]] = defaultdict(list)
    for t in tasks:
        categories[(t.category, t.subcategory)].append(t)
    category_rows = []
    for (cat, sub), items in sorted(categories.items(), key=lambda kv: -len(kv[1]))[:12]:
        est = np.asarray([t.estimate_hours for t in items])
        act = np.asarray([t.actual_hours for t in items])
        category_rows.append(
            {
                "category": cat,
                "subcategory": sub,
                "n_tasks": len(items),
                "median_estimate": round(float(np.median(est)), 2),
                "median_actual": round(float(np.median(act)), 2),
                "median_ratio": round(float(np.median(act / est)), 3),
                "share_underestimated": round(float(np.mean(act > est)) * 100, 1),
            }
        )
    deciles = [0.1, 0.25, 0.5, 0.75, 0.9]
    return {
        **DATASET_INFO,
        "n_tasks": len(tasks),
        "n_projects": len({t.project for t in tasks}),
        "period": f"{tasks[0].estimated_on.isoformat()} .. {tasks[-1].estimated_on.isoformat()}",
        "share_exact_estimates": round(float(np.mean(ratios == 1.0)) * 100, 1),
        "task_ratio_quantiles": {f"p{int(p * 100)}": round(float(np.quantile(ratios, p)), 3) for p in deciles},
        "aggregate_ratio_quantiles": {
            f"p{int(p * 100)}": round(float(np.quantile(agg_ratios, p)), 3) for p in deciles
        },
        "n_aggregates": len(aggregates),
        "categories": category_rows,
        "aggregates": [
            {
                "aggregate_id": a.aggregate_id,
                "n_tasks": a.n_tasks,
                "estimate_hours": a.estimate_hours,
                "actual_hours": a.actual_hours,
                "ratio": round(a.ratio, 3),
                "first_estimated_on": a.first_estimated_on.isoformat(),
                "last_estimated_on": a.last_estimated_on.isoformat(),
            }
            for a in aggregates
        ],
    }
