"""Choose the hierarchical correction model on TRAINING years only, then test it once.

  search  - fit on tasks estimated 2004-2009, score on 2010 (validation inside the training period);
            every candidate is printed and the best is recorded in datasets/eval/sip_model_choice.json.
  test    - fit the recorded choice on everything estimated before 2011 and score 2011-2014 once,
            next to the human estimate and the shipped size-only model. Appends to the journal.
Features available when a task is estimated: category, sub-category, project, assignee, raiser,
authoriser, priority, size bucket, whether the estimate is a "round" number.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.empirical import DATASET_DIR, HOLDOUT_CUTOFF, RatioQuantileModel, _bucket, load_sip_tasks  # noqa: E402
from parallax.evaluation.benchmark import standardized_accuracy, wilcoxon_signed_rank  # noqa: E402
from parallax.hierarchical import HierarchicalRatioModel  # noqa: E402

CHOICE = ROOT / "datasets" / "eval" / "sip_model_choice.json"
RESULT = ROOT / "datasets" / "eval" / "sip_model_test.json"
VALIDATION_START = date(2010, 1, 1)
ROUND = {0.5, 1, 2, 3, 4, 5, 6, 7, 7.5, 8, 10, 12, 14, 15, 16, 20, 21, 24, 28, 30, 35, 40, 50, 60, 70, 80, 100}
FACTORS = ("bucket", "category", "subcategory", "project", "assignee", "raiser", "authoriser", "priority", "round")


def fine_bucket(e: float) -> str:
    return str(min(9, max(0, int(math.floor(math.log2(max(e, 0.25)) + 2)))))


def features() -> dict[str, dict[str, str]]:
    out = {}
    with open(DATASET_DIR / "Sip-task-info.csv", encoding="latin-1", newline="") as f:
        for r in csv.DictReader(f):
            if r["TaskNumber"] in out:
                continue
            out[r["TaskNumber"]] = {"category": r["Category"], "subcategory": f"{r['Category']}/{r['SubCategory']}",
                                    "project": r["ProjectCode"], "assignee": r["AssignedToID"],
                                    "raiser": r["RaisedByID"], "authoriser": r["AuthorisedByID"],
                                    "priority": r["Priority"]}
    return out


def rows_for(tasks, feats):
    rows = []
    for t in tasks:
        x = dict(feats.get(t.task_id, {}))
        x["bucket"] = fine_bucket(t.estimate_hours)
        x["round"] = "round" if t.estimate_hours in ROUND else "odd"
        rows.append((t.estimate_hours, t.actual_hours, x))
    return rows


def metrics(test_rows, preds, human=False) -> dict:
    a = np.array([r[1] for r in test_rows])
    p = np.array([q[1] for q in preds])
    err = np.abs(a - p)
    out = {"n": len(a), "mae": round(float(err.mean()), 3), "mdae": round(float(np.median(err)), 3),
           "sa": round(standardized_accuracy(a, p), 2), "pred_25": round(float(np.mean(err / a <= 0.25) * 100), 2),
           "mdape": round(float(np.median(err / a) * 100), 2)}
    if not human:
        out["coverage_p10_p90"] = round(float(np.mean([(q[0] <= x <= q[2]) for q, x in zip(preds, a)]) * 100), 2)
        out["mean_width"] = round(float(np.mean([q[2] - q[0] for q in preds])), 2)
    return out


def size_only(train_rows, test_rows):
    m = RatioQuantileModel.fit([(e, a) for e, a, _ in train_rows])
    return [m.predict(e) for e, _, _ in test_rows]


def hier(train_rows, test_rows, factors, k):
    m = HierarchicalRatioModel(tuple(factors), shrinkage=k, bucket_of=lambda e: str(_bucket(e))).fit(train_rows)
    return [m.predict(e, x) for e, _, x in test_rows]


def cmd_search(_args) -> int:
    tasks = load_sip_tasks()
    feats = features()
    train = rows_for([t for t in tasks if t.estimated_on < VALIDATION_START], feats)
    val = rows_for([t for t in tasks if VALIDATION_START <= t.estimated_on < HOLDOUT_CUTOFF], feats)
    print(f"train {len(train)} (2004-2009), validation {len(val)} (2010)")
    results = [{"model": "human", **metrics(val, [(e, e, e) for e, _, _ in val], human=True)},
               {"model": "size-only (shipped)", **metrics(val, size_only(train, val))}]
    candidates = [("bucket",), ("bucket", "category"), ("bucket", "subcategory"), ("bucket", "project"),
                  ("bucket", "assignee"), ("bucket", "subcategory", "project"),
                  ("bucket", "subcategory", "project", "assignee"),
                  ("bucket", "subcategory", "project", "assignee", "priority", "round"),
                  ("bucket", "subcategory", "project", "assignee", "raiser", "authoriser", "priority", "round")]
    for factors, k in itertools.product(candidates, (5, 20, 50)):
        results.append({"model": f"hier[{'+'.join(factors)}] k={k}", "factors": list(factors), "k": k,
                        **metrics(val, hier(train, val, factors, k))})
    for r in results:
        print(f"{r['model']:75} MAE {r['mae']:7} SA {r['sa']:6} PRED25 {r['pred_25']:6} cov {r.get('coverage_p10_p90', '-')}")
    eligible = [r for r in results if "factors" in r and r["coverage_p10_p90"] >= 75]
    best = min(eligible, key=lambda r: r["mae"])
    CHOICE.write_text(json.dumps({"rule": "lowest validation MAE among candidates with P10-P90 coverage >= 75%",
                                  "validation": "fit 2004-2009, score 2010 (all inside the training period)",
                                  "chosen": best, "candidates": results}, indent=1) + "\n", encoding="utf-8")
    print("chosen:", best["model"])
    return 0


def cmd_test(args) -> int:
    choice = json.loads(CHOICE.read_text(encoding="utf-8"))["chosen"]
    tasks = load_sip_tasks()
    feats = features()
    train = rows_for([t for t in tasks if t.estimated_on < HOLDOUT_CUTOFF], feats)
    test = rows_for([t for t in tasks if t.estimated_on >= HOLDOUT_CUTOFF], feats)
    human = [(e, e, e) for e, _, _ in test]
    so = size_only(train, test)
    hi = hier(train, test, choice["factors"], choice["k"])
    a = [r[1] for r in test]
    err = lambda preds: [abs(x - q[1]) for x, q in zip(a, preds)]  # noqa: E731
    w_h = wilcoxon_signed_rank(err(human), err(hi))
    w_s = wilcoxon_signed_rank(err(so), err(hi))
    rng = np.random.default_rng(20261018)
    eh, es, ei = np.array(err(human)), np.array(err(so)), np.array(err(hi))
    boots = [(float(es[i].mean() - ei[i].mean())) for i in (rng.integers(0, len(a), len(a)) for _ in range(5000))]
    report = {
        "chosen": choice["model"], "train": f"estimated before {HOLDOUT_CUTOFF} ({len(train)})", "test": len(test),
        "human": metrics(test, human, human=True), "size_only": metrics(test, so), "hierarchical": metrics(test, hi),
        "wilcoxon_hier_vs_human_p": float(f"{w_h['p_value']:.3g}"), "wilcoxon_hier_vs_size_only_p": float(f"{w_s['p_value']:.3g}"),
        "mae_gain_vs_size_only_95ci": [round(float(x), 3) for x in np.quantile(boots, [0.025, 0.975])],
    }
    RESULT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    if not args.no_journal:
        entry = {"date": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes"),
                 "tag": "sip_hierarchical_holdout", "labels": "SiP 2011-2014 (2,248 tasks)", "rules_version": None,
                 "model": None,
                 "summary": [{"reader": "human", **report["human"], "coverage_p10_p90": None},
                             {"reader": "size-only", **report["size_only"]},
                             {"reader": "hierarchical", **report["hierarchical"],
                              "wilcoxon_vs_human_p": report["wilcoxon_hier_vs_human_p"]}],
                 "note": f"Hierarchical correction chosen on 2010 validation only ({choice['model']}), fitted on "
                         f"pre-2011, tested once on 2011-2014. Wilcoxon vs size-only p={report['wilcoxon_hier_vs_size_only_p']}, "
                         f"MAE gain vs size-only CI {report['mae_gain_vs_size_only_95ci']} h."}
        with open(ROOT / "datasets" / "eval" / "journal.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["search", "test"])
    ap.add_argument("--no-journal", action="store_true")
    args = ap.parse_args()
    return {"search": cmd_search, "test": cmd_test}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
