"""Replay 2011-2014 of a real software company as if PARALLAX had been operating there.

Unlike a fixed train/test split, every estimate is made on the day the task was estimated,
using only tasks that had *already been completed* by that day (SiP records EstimateOn and
CompletedOn). Actual hours become learning data the day the task completes. This is the
closest public-data equivalent of running the product in production.

Modes compared on every task estimated from 2011-01-01:
  human     the developer's own estimate (what the company actually used)
  frozen    ratio model fitted once on tasks completed before 2011, never updated
  online    ratio model refitted every day on everything completed so far (what the app does)
  online+jev  (Development tasks >= 20 h read by Jev) ratio quantiles per Jev overrun group,
            learned online from completed read tasks; groups use the SiP training thresholds
Metrics: MAE, MdAE, SA (vs random guessing), PRED(25), P10-P90 coverage, Wilcoxon vs human.
No AI calls; Jev readings come from datasets/eval/sip_jev_readings.json.
Usage: python scripts/sip_operational_replay.py [--no-journal]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.empirical import DATASET_DIR, RatioQuantileModel, load_sip_tasks  # noqa: E402
from parallax.evaluation.benchmark import standardized_accuracy, wilcoxon_signed_rank  # noqa: E402

START = date(2011, 1, 1)
OUT = ROOT / "datasets" / "eval" / "sip_operational_replay.json"
READINGS = ROOT / "datasets" / "eval" / "sip_jev_readings.json"
STUDY = ROOT / "datasets" / "eval" / "sip_jev_study.json"
MIN_GROUP = 30


def completion_dates() -> dict[str, date]:
    out = {}
    with open(DATASET_DIR / "est-act-dates.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                out[row["TaskNumber"]] = datetime.strptime(row["CompletedOn"].strip(), "%d-%b-%y").date()
            except ValueError:
                pass
    return out


def metrics(preds: list[tuple[float, float, float, float]], human_err=None) -> dict:
    a = np.array([p[0] for p in preds])
    p50 = np.array([p[2] for p in preds])
    err = np.abs(a - p50)
    out = {
        "n": len(preds),
        "mae": round(float(err.mean()), 2),
        "mdae": round(float(np.median(err)), 2),
        "sa": round(standardized_accuracy(a, p50), 1),
        "pred_25": round(float(np.mean(err / a <= 0.25) * 100), 1),
        "coverage_p10_p90": round(float(np.mean([(p[1] <= p[0] <= p[3]) for p in preds]) * 100), 1)
        if preds[0][1] != preds[0][3] else None,
    }
    if human_err is not None:
        w = wilcoxon_signed_rank(human_err, err)
        out["wilcoxon_vs_human_p"] = float(f"{w['p_value']:.3g}") if w["p_value"] is not None else None
        out["effect_vs_human"] = round(w["effect_size"], 3) if w["effect_size"] is not None else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-journal", action="store_true")
    args = ap.parse_args()
    done_on = completion_dates()
    tasks = [t for t in load_sip_tasks() if t.task_id in done_on]
    by_completion = sorted(tasks, key=lambda t: done_on[t.task_id])
    completion_keys = [done_on[t.task_id] for t in by_completion]
    test = [t for t in tasks if t.estimated_on >= START]
    pre = [t for t in by_completion if done_on[t.task_id] < START]
    frozen = RatioQuantileModel.fit([(t.estimate_hours, t.actual_hours) for t in pre])

    readings = json.loads(READINGS.read_text(encoding="utf-8"))
    tag = json.loads(STUDY.read_text(encoding="utf-8"))["report"]["question"]
    lo, hi = json.loads(STUDY.read_text(encoding="utf-8"))["report"]["thresholds_from_train"]

    def group(tid):
        p = readings.get(tid, {}).get(tag)
        return None if p is None else int(p > lo) + int(p > hi)

    def jev_population(t):
        return t.category == "Development" and t.estimate_hours >= 20 and group(t.task_id) is not None

    rows = {"human": [], "frozen": [], "online": []}
    jev_rows = {"human": [], "online": [], "online+jev": []}
    yearly = defaultdict(lambda: {"human": [], "frozen": [], "online": []})
    cache: dict[date, tuple] = {}
    for t in sorted(test, key=lambda x: x.estimated_on):
        day = t.estimated_on
        if day not in cache:
            known = by_completion[: bisect_left(completion_keys, day)]  # completed strictly before that day
            model = RatioQuantileModel.fit([(k.estimate_hours, k.actual_hours) for k in known])
            jev_known = [k for k in known if jev_population(k)]
            pooled = np.sort([k.actual_hours / k.estimate_hours for k in jev_known])
            groups = {g: np.sort([k.actual_hours / k.estimate_hours for k in jev_known if group(k.task_id) == g])
                      for g in range(3)}
            cache = {day: (model, pooled, groups)}  # tasks arrive in date order: keep only today's fit
        model, pooled, groups = cache[day]
        e, a = t.estimate_hours, t.actual_hours
        f = frozen.predict(e)
        o = model.predict(e)
        rows["human"].append((a, e, e, e))
        rows["frozen"].append((a, *f))
        rows["online"].append((a, *o))
        for name, pred in (("human", (a, e, e, e)), ("frozen", (a, *f)), ("online", (a, *o))):
            yearly[day.year][name].append(pred)
        if jev_population(t) and len(pooled) >= MIN_GROUP:
            g = group(t.task_id)
            ratios = groups[g] if len(groups[g]) >= MIN_GROUP else pooled
            q = np.quantile(ratios, [0.1, 0.5, 0.9])
            qp = np.quantile(pooled, [0.1, 0.5, 0.9])
            jev_rows["human"].append((a, e, e, e))
            jev_rows["online"].append((a, *(e * qp)))
            jev_rows["online+jev"].append((a, *(e * q)))

    human_err = [abs(r[0] - r[2]) for r in rows["human"]]
    jev_human_err = [abs(r[0] - r[2]) for r in jev_rows["human"]]
    report = {
        "what": "Operational replay of SiP 2011-2014: each estimate uses only tasks completed before its estimate date",
        "all_tasks": {k: metrics(v, None if k == "human" else human_err) for k, v in rows.items()},
        "dev_tasks_20h_read_by_jev": {k: metrics(v, None if k == "human" else jev_human_err)
                                      for k, v in jev_rows.items()},
        "by_year": [{"year": y, "n": len(v["human"]), **{k: round(float(np.mean([abs(p[0] - p[2]) for p in v[k]])), 2)
                                                          for k in ("human", "frozen", "online")}}
                    for y, v in sorted(yearly.items())],
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not args.no_journal:
        summary = [{"reader": k, **v} for k, v in report["all_tasks"].items()] + \
                  [{"reader": f"dev>=20h {k}", **v} for k, v in report["dev_tasks_20h_read_by_jev"].items()]
        entry = {"date": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes"),
                 "tag": "sip_operational_replay", "labels": "SiP 2011-2014, completion-date aware",
                 "rules_version": None, "model": "jev-1.13.0 (cached)", "summary": summary,
                 "note": "Production replay: every estimate uses only work completed before its estimate date. "
                         "Online = refit daily (what the app does); frozen = fitted on work completed before 2011."}
        with open(ROOT / "datasets" / "eval" / "journal.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
