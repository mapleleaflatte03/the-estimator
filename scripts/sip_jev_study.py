"""Can Jev, reading only a task's text, tell which human estimates will overrun?

Data: SiP (10,022 real tasks with the hours estimated before work and the hours
actually spent). Population: Development tasks estimated at >= 20 h, where most
of the absolute error lives. Each task summary is read by Jev with yes/no
questions an experienced estimator would ask; answers are probabilities.

Protocol (no test data is ever used to choose anything):
  pilot  - ask every candidate question on a random sample of *training* tasks
           (estimated before 2011); pick the question whose answer correlates best
           with log(actual / estimate). Recorded in the journal.
  full   - ask the chosen question(s) on the remaining training tasks and on all
           test tasks (2011-2014).
  report - fit ratio quantiles on training tasks only: (a) pooled, as the current
           app does for this size; (b) split by Jev's answer, thresholds taken from
           training data; compare both and the raw human estimate on the test tasks.

Only task ids and Jev's probabilities are stored (datasets/eval/sip_jev_readings.json);
the SiP text itself is never copied (CC BY-NC-ND 4.0).
Usage: python scripts/sip_jev_study.py pilot|full|report [--max-calls N]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.empirical import HOLDOUT_CUTOFF, load_sip_tasks  # noqa: E402
from parallax.jev import OVERRUN_Q, JevReader, Question, load_dotenv  # noqa: E402

MIN_ESTIMATE = 20.0
PILOT_SIZE = 75
SEED = 20261017
CACHE = ROOT / "datasets" / "jev_cache" / "sip_answers.json"
READINGS = ROOT / "datasets" / "eval" / "sip_jev_readings.json"
STUDY = ROOT / "datasets" / "eval" / "sip_jev_study.json"

CANDIDATES = {
    "open_scope": Question(
        "open_scope", "v1", "noul",
        "Is the work described in `{ref}` open-ended or loosely defined, so that its real size will only "
        "become clear once work has started?"),
    "new_build": Question(
        "new_build", "v1", "noul",
        "Does `{ref}` ask for building something new (new logic, a new module or new behaviour) rather than "
        "changing, fixing or configuring something that already exists?"),
    "coupling": Question(
        "coupling", "v1", "noul",
        "Does `{ref}` involve moving, converting or reconciling data, or depend on another system, team or "
        "company outside the developer's control?"),
    "overrun": OVERRUN_Q,  # identical object to the question asked of every brief clause in the app
}


def population():
    tasks = [t for t in load_sip_tasks() if t.category == "Development" and t.estimate_hours >= MIN_ESTIMATE]
    train = [t for t in tasks if t.estimated_on < HOLDOUT_CUTOFF]
    test = [t for t in tasks if t.estimated_on >= HOLDOUT_CUTOFF]
    return train, test


def pilot_sample(train):
    rng = random.Random(SEED)
    return rng.sample(train, PILOT_SIZE)


def reader() -> JevReader:
    load_dotenv()
    return JevReader(cache_path=CACHE, max_calls_per_hour=None, questions=())


def save_readings(r: JevReader, tasks, questions) -> dict:
    data = json.loads(READINGS.read_text(encoding="utf-8")) if READINGS.exists() else {}
    for t in tasks:
        row = data.setdefault(t.task_id, {})
        for q in questions:
            a = r.answer(t.summary, q)
            if a:
                row[q.tag] = a["answer"]["noul"]
                row.setdefault("model", a.get("model"))
    READINGS.write_text(json.dumps(data, indent=0, sort_keys=True), encoding="utf-8")
    return data


def spearman(x, y) -> float:
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def auc(scores, labels) -> float:
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return float(wins / (len(pos) * len(neg)))


def journal(tag: str, summary, note: str, model=None) -> None:
    entry = {"date": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes"), "tag": tag,
             "labels": "SiP Development tasks >= 20h (real actuals)", "rules_version": None, "model": model,
             "summary": summary, "note": note}
    with open(ROOT / "datasets" / "eval" / "journal.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_pilot(args) -> int:
    train, test = population()
    sample = pilot_sample(train)
    r = reader()
    qs = list(CANDIDATES.values())
    todo = r.missing([t.summary for t in sample], qs)
    print(f"population: train {len(train)}, test {len(test)}; pilot {len(sample)} tasks, {len(todo)} questions to ask")
    r.ask([t.summary for t in sample], qs, max_calls=args.max_calls)
    print("status:", {k: v for k, v in r.status().items() if k != "keys"})
    data = save_readings(r, sample, qs)
    y = np.log([t.actual_hours / t.estimate_hours for t in sample])
    over = [t.actual_hours > 1.25 * t.estimate_hours for t in sample]
    rows = []
    for name, q in CANDIDATES.items():
        pairs = [(data[t.task_id].get(q.tag), yi, oi) for t, yi, oi in zip(sample, y, over)
                 if data.get(t.task_id, {}).get(q.tag) is not None]
        if len(pairs) < 20:
            continue
        p = np.array([a for a, _, _ in pairs])
        rows.append({"question": q.tag, "n": len(pairs), "spearman_log_ratio": round(spearman(p, [b for _, b, _ in pairs]), 3),
                     "auc_overrun_25pct": round(auc(p, [c for _, _, c in pairs]), 3),
                     "mean_p": round(float(p.mean()), 3)})
    for row in rows:
        print(row)
    if len(rows) < len(CANDIDATES) or any(row["n"] < PILOT_SIZE for row in rows):
        print("pilot incomplete; nothing recorded")
        return 1
    chosen = args.choose or max(rows, key=lambda r_: r_["spearman_log_ratio"])["question"]
    reason = args.reason or "highest Spearman with log(actual/estimate)"
    STUDY.write_text(json.dumps({"pilot": {"seed": SEED, "size": PILOT_SIZE, "candidates": rows,
                                           "chosen": chosen, "reason": reason}}, indent=2) + "\n", encoding="utf-8")
    journal("sip_jev_pilot", rows, f"Pilot on {PILOT_SIZE} TRAINING tasks only (estimated before 2011), test tasks "
            f"untouched. Chosen: {chosen}. Reason: {reason}", model="jev-1.13.0")
    return 0


def cmd_full(args) -> int:
    study = json.loads(STUDY.read_text(encoding="utf-8"))
    chosen = [q for q in CANDIDATES.values() if q.tag in (args.questions or [study["pilot"]["chosen"]])]
    train, test = population()
    r = reader()
    texts = [t.summary for t in train + test]
    todo = r.missing(texts, chosen)
    print(f"{len(todo)} questions to ask ({-(-len(todo) // 5)} calls) for {[q.tag for q in chosen]}")
    r.ask(texts, chosen, max_calls=args.max_calls)
    print("status:", {k: v for k, v in r.status().items() if k != "keys"})
    save_readings(r, train + test, chosen)
    left = r.missing(texts, chosen)
    print(f"still missing: {len(left)}")
    return 0 if not left else 1


def quantile_model(pairs):
    return np.sort(np.asarray([a / e for e, a in pairs]))


def evaluate(preds):
    """preds: list of (actual, p10, p50, p90)."""
    a = np.array([p[0] for p in preds])
    p50 = np.array([p[2] for p in preds])
    err = np.abs(a - p50)
    return {
        "n": len(preds),
        "mae": round(float(err.mean()), 2),
        "mdape": round(float(np.median(err / a) * 100), 1),
        "pred_25": round(float(np.mean(err / a <= 0.25) * 100), 1),
        "coverage_p10_p90": round(float(np.mean([(p[1] <= p[0] <= p[3]) for p in preds]) * 100), 1),
    }


def cmd_report(args) -> int:
    study = json.loads(STUDY.read_text(encoding="utf-8"))
    tag = args.question or study["pilot"]["chosen"]
    data = json.loads(READINGS.read_text(encoding="utf-8"))
    train, test = population()
    train = [t for t in train if tag in data.get(t.task_id, {})]
    test_all = test
    test = [t for t in test if tag in data.get(t.task_id, {})]
    print(f"{tag}: train {len(train)} read, test {len(test)}/{len(test_all)} read")
    pooled = quantile_model([(t.estimate_hours, t.actual_hours) for t in train])
    p_train = np.array([data[t.task_id][tag] for t in train])
    # Split thresholds from training data only: tertiles of Jev's probability.
    cuts = [float(x) for x in np.quantile(p_train, [1 / 3, 2 / 3])]

    def group(p: float) -> int:
        return int(p > cuts[0]) + int(p > cuts[1])

    by_group = {g: quantile_model([(t.estimate_hours, t.actual_hours) for t, p in zip(train, p_train) if group(p) == g])
                for g in range(3)}
    groups_train = [{"group": g, "n_train": len(v), "ratio_p10": round(float(np.quantile(v, .1)), 3),
                     "ratio_p50": round(float(np.quantile(v, .5)), 3), "ratio_p90": round(float(np.quantile(v, .9)), 3)}
                    for g, v in by_group.items()]

    def predict(model, est):
        q = np.quantile(model, [0.1, 0.5, 0.9])
        return [est * x for x in q]

    human, base, jev = [], [], []
    for t in test:
        p = data[t.task_id][tag]
        human.append((t.actual_hours, t.estimate_hours, t.estimate_hours, t.estimate_hours))
        base.append((t.actual_hours, *predict(pooled, t.estimate_hours)))
        jev.append((t.actual_hours, *predict(by_group[group(p)], t.estimate_hours)))
    res_h, res_b, res_j = evaluate(human), evaluate(base), evaluate(jev)
    res_h["coverage_p10_p90"] = None
    # Paired bootstrap of the MAE difference (calibrated pooled - calibrated with Jev).
    rng = np.random.default_rng(SEED)
    eb = np.abs(np.array([x[0] - x[2] for x in base]))
    ej = np.abs(np.array([x[0] - x[2] for x in jev]))
    diffs = []
    for _ in range(5000):
        idx = rng.integers(0, len(eb), len(eb))
        diffs.append(eb[idx].mean() - ej[idx].mean())
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    p_test = np.array([data[t.task_id][tag] for t in test])
    y_test = np.log([t.actual_hours / t.estimate_hours for t in test])
    test_groups = []
    for g in range(3):
        idx = [i for i, p in enumerate(p_test) if group(p) == g]
        if idx:
            test_groups.append({"group": g, "n_test": len(idx),
                                "test_ratio_p50": round(float(np.exp(np.median(y_test[idx]))), 3)})
    report = {
        "question": tag,
        "population": f"SiP Development tasks with estimate >= {MIN_ESTIMATE:g} h",
        "train": f"estimated before {HOLDOUT_CUTOFF.isoformat()} ({len(train)} tasks)",
        "test": f"estimated {HOLDOUT_CUTOFF.isoformat()} or later ({len(test)} tasks)",
        "thresholds_from_train": [round(c, 4) for c in cuts],
        "pooled_train_ratio_p50": round(float(np.quantile(pooled, 0.5)), 4),
        "groups_train": groups_train,
        "groups_test": test_groups,
        "spearman_test": round(spearman(p_test, y_test), 3),
        "auc_overrun_25pct_test": round(auc(p_test, [t.actual_hours > 1.25 * t.estimate_hours for t in test]), 3),
        "human_estimate": res_h,
        "calibrated_size_only": res_b,
        "calibrated_with_jev": res_j,
        "mae_gain_vs_size_only_h": round(float(eb.mean() - ej.mean()), 2),
        "mae_gain_95ci_h": [round(float(lo), 2), round(float(hi), 2)],
    }
    study["report"] = report
    STUDY.write_text(json.dumps(study, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    summary = [{"reader": "human", **res_h}, {"reader": "size-only", **res_b}, {"reader": f"jev:{tag}", **res_j}]
    if args.no_journal:
        return 0
    journal(args.tag or "sip_jev_holdout", summary,
            f"Held-out test 2011-2014. Jev {tag} tertile split fitted on training tasks only. "
            f"MAE gain vs size-only {report['mae_gain_vs_size_only_h']} h (95% CI {report['mae_gain_95ci_h']}); "
            f"test Spearman {report['spearman_test']}, AUC {report['auc_overrun_25pct_test']}.", model="jev-1.13.0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["pilot", "full", "report"])
    ap.add_argument("--max-calls", type=int, default=None)
    ap.add_argument("--questions", nargs="*")
    ap.add_argument("--question")
    ap.add_argument("--tag")
    ap.add_argument("--choose", help="pilot: override the chosen question tag (record --reason)")
    ap.add_argument("--reason")
    ap.add_argument("--no-journal", action="store_true", help="report: rewrite the study file only (no new run)")
    args = ap.parse_args()
    return {"pilot": cmd_pilot, "full": cmd_full, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
