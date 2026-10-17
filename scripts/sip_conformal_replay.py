"""Do the hour ranges stay honest for every size of work, in production conditions?

Production replay (each estimate uses only work *completed* before its estimate date) of the
online ratio model, with and without adaptive conformal levels per size bucket
(parallax/conformal.py). Outcomes update the level on the day the task completes.

  select - replay 2008-2010 (training period) for several gamma values; choose the gamma whose
           worst size bucket is closest to 80% coverage (ties: narrower ranges). Recorded.
  test   - replay 2011-2014 once with the recorded gamma. Appends to the journal.
"""
from __future__ import annotations

import argparse
import heapq
import json
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "scripts"))

from parallax.conformal import AdaptiveLevel  # noqa: E402
from parallax.empirical import RatioQuantileModel, bucket_label, _bucket, load_sip_tasks  # noqa: E402
from sip_operational_replay import completion_dates  # noqa: E402

CHOICE = ROOT / "datasets" / "eval" / "sip_conformal_choice.json"
RESULT = ROOT / "datasets" / "eval" / "sip_conformal_test.json"
GAMMAS = (0.0, 0.002, 0.005, 0.01, 0.02, 0.05)


def replay(start: date, end: date, gammas) -> dict:
    done_on = completion_dates()
    tasks = [t for t in load_sip_tasks() if t.task_id in done_on]
    by_completion = sorted(tasks, key=lambda t: done_on[t.task_id])
    keys = [done_on[t.task_id] for t in by_completion]
    period = sorted((t for t in tasks if start <= t.estimated_on < end), key=lambda t: t.estimated_on)
    levels = {g: AdaptiveLevel(gamma=g) for g in gammas}
    pending: dict[float, list] = {g: [] for g in gammas}
    hits = {g: defaultdict(list) for g in gammas}
    widths = {g: defaultdict(list) for g in gammas}
    model, fitted_on = None, None
    seq = 0
    for t in period:
        day = t.estimated_on
        if fitted_on != day:
            known = by_completion[: bisect_left(keys, day)]
            model, fitted_on = RatioQuantileModel.fit([(k.estimate_hours, k.actual_hours) for k in known]), day
        grp = bucket_label(_bucket(t.estimate_hours))
        ratios = model.ratios_for(t.estimate_hours)
        for g in gammas:
            lv, heap = levels[g], pending[g]
            while heap and heap[0][0] < day:  # outcomes known before this estimate
                _, _, b, lo, hi, act = heapq.heappop(heap)
                lv.update(b, lo, hi, act)
            q = np.quantile(ratios, lv.probs(grp))
            lo, hi = t.estimate_hours * q[0], t.estimate_hours * q[2]
            seq += 1
            heapq.heappush(heap, (done_on[t.task_id], seq, grp, lo, hi, t.actual_hours))
            hits[g][grp].append(lo <= t.actual_hours <= hi)
            widths[g][grp].append(hi - lo)
    out = {}
    for g in gammas:
        per = {b: {"n": len(v), "coverage": round(float(np.mean(v)) * 100, 1),
                   "mean_width_h": round(float(np.mean(widths[g][b])), 1)} for b, v in hits[g].items()}
        allv = [x for v in hits[g].values() for x in v]
        out[str(g)] = {"overall_coverage": round(float(np.mean(allv)) * 100, 1),
                       "worst_bucket_gap": round(max(abs(p["coverage"] - 80) for p in per.values()), 1),
                       "mean_width_h": round(float(np.mean([x for v in widths[g].values() for x in v])), 1),
                       "by_bucket": dict(sorted(per.items(), key=lambda kv: kv[0]))}
    return out


def journal(tag, summary, note):
    entry = {"date": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes"), "tag": tag,
             "labels": "SiP production replay (completion-date aware)", "rules_version": None, "model": None,
             "summary": summary, "note": note}
    with open(ROOT / "datasets" / "eval" / "journal.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_select(_args) -> int:
    res = replay(date(2008, 1, 1), date(2011, 1, 1), GAMMAS)
    for g, r in res.items():
        print(g, {k: r[k] for k in ("overall_coverage", "worst_bucket_gap", "mean_width_h")},
              {b: v["coverage"] for b, v in r["by_bucket"].items()})
    best = min(res, key=lambda g: (res[g]["worst_bucket_gap"], res[g]["mean_width_h"]))
    CHOICE.write_text(json.dumps({"rule": "smallest worst-bucket |coverage - 80|, ties: narrower", "period": "2008-2010",
                                  "chosen_gamma": float(best), "candidates": res}, indent=1) + "\n", encoding="utf-8")
    journal("sip_conformal_select", [{"reader": f"gamma {g}", **{k: r[k] for k in ("overall_coverage", "worst_bucket_gap", "mean_width_h")}}
                                     for g, r in res.items()],
            f"Choosing the adaptive-conformal step on the training period only (replay 2008-2010). Chosen gamma {best}.")
    print("chosen gamma", best)
    return 0


def cmd_test(_args) -> int:
    g = json.loads(CHOICE.read_text(encoding="utf-8"))["chosen_gamma"]
    res = replay(date(2011, 1, 1), date(2015, 1, 1), (0.0, g))
    report = {"gamma": g, "without": res["0.0"], "with": res[str(g)]}
    RESULT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    journal("sip_conformal_holdout",
            [{"reader": "fixed ranges", **{k: res["0.0"][k] for k in ("overall_coverage", "worst_bucket_gap", "mean_width_h")}},
             {"reader": f"adaptive (gamma {g})", **{k: res[str(g)][k] for k in ("overall_coverage", "worst_bucket_gap", "mean_width_h")}}],
            "Held-out production replay 2011-2014, gamma fixed on 2008-2010. Coverage by size bucket: "
            + "; ".join(f"{b}: {res['0.0']['by_bucket'][b]['coverage']}% -> {res[str(g)]['by_bucket'][b]['coverage']}%"
                        for b in res["0.0"]["by_bucket"]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["select", "test"])
    args = ap.parse_args()
    return {"select": cmd_select, "test": cmd_test}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
