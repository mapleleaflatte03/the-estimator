"""Evaluate locked predictions and validate proposed calibration changes.

Only validation results can approve a calibration candidate. The untouched
final test split must not be used to tune or select model changes.
"""
from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class PredictionRecord:
    case_id: str
    actual_hours: float
    pred_p50: float
    pred_low: float          # P10 for an illustrative 80% central interval
    pred_high: float         # P90


@dataclass(frozen=True)
class BenchmarkMetrics:
    model_name: str
    split: str
    case_ids: tuple[str, ...]
    n_cases: int
    mae: float
    mdape: float
    wape: float
    pred_25: float
    interval_coverage: float
    mean_interval_width: float


def evaluate_predictions(
    model_name: str, records: Sequence[PredictionRecord], split: str = "validation"
) -> BenchmarkMetrics:
    if not records:
        raise ValueError("Cannot evaluate an empty dataset")
    if split not in {"train", "validation", "test"}:
        raise ValueError("split must be train, validation or test")
    if len({r.case_id for r in records}) != len(records):
        raise ValueError("case_id must be unique")
    for r in records:
        vals = (r.actual_hours, r.pred_p50, r.pred_low, r.pred_high)
        if not all(math.isfinite(x) for x in vals):
            raise ValueError("Non-finite prediction")
        if r.actual_hours <= 0 or r.pred_low < 0 or not r.pred_low <= r.pred_p50 <= r.pred_high:
            raise ValueError(f"Invalid record: {r.case_id}")
    actuals = np.array([r.actual_hours for r in records], dtype=float)
    point = np.array([r.pred_p50 for r in records], dtype=float)
    lows = np.array([r.pred_low for r in records], dtype=float)
    highs = np.array([r.pred_high for r in records], dtype=float)
    abs_errors = np.abs(actuals - point)
    ape = abs_errors / actuals
    covered = (actuals >= lows) & (actuals <= highs)
    return BenchmarkMetrics(
        model_name=model_name,
        split=split,
        case_ids=tuple(sorted(r.case_id for r in records)),
        n_cases=len(records),
        mae=float(np.mean(abs_errors)),
        mdape=float(np.median(ape) * 100),
        wape=float(np.sum(abs_errors) / np.sum(actuals) * 100),
        pred_25=float(np.mean(ape <= 0.25) * 100),
        interval_coverage=float(np.mean(covered) * 100),
        mean_interval_width=float(np.mean(highs - lows)),
    )


def calibration_gate_decision(
    before: BenchmarkMetrics,
    after: BenchmarkMetrics,
    min_coverage: float = 75.0,
    min_cases: int = 20,
) -> dict:
    """Prototype gate, not a statistical significance test.

    Select on a *fixed* validation dataset and avoid repeatedly testing many
    candidates on it. Run final holdout test only after model selection.
    """
    if before.split != "validation" or after.split != "validation":
        raise ValueError("Calibration gate must use validation split only")
    if before.case_ids != after.case_ids:
        raise ValueError("Compare predictions on precisely the same case IDs")
    if not 0 <= min_coverage <= 100:
        raise ValueError("Invalid coverage threshold")
    if before.n_cases < min_cases:
        return {"accepted": False, "reason": f"Insufficient validation cases ({before.n_cases} < {min_cases})"}
    improved = after.mae < before.mae - 1e-9
    coverage_ok = after.interval_coverage >= min_coverage
    # WAPE is proportional to MAE if cases/actuals are identical; included as a report.
    accepted = bool(improved and coverage_ok)
    reasons = []
    if not improved:
        reasons.append("MAE did not improve")
    if not coverage_ok:
        reasons.append("Validation interval coverage below threshold")
    return {
        "accepted": accepted,
        "reason": "PASS on validation (not proof of future improvement)" if accepted else "; ".join(reasons),
        "delta_mae": after.mae - before.mae,
        "delta_mdape": after.mdape - before.mdape,
        "coverage_after": after.interval_coverage,
    }
