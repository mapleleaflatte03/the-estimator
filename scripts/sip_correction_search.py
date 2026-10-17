"""SiP hour corrections. The protocol file is the authority; this script only carries it out.

  select  Fit on tasks estimated before 2010 and score 2010. Writes the choice file.
          Appends a journal line only when nobody is promoted.
  test    Score 2011-2014 once, and only for a promoted candidate whose choice file is
          already committed. Refuses otherwise.

Does not call Jev. Does not edit application code. Does not overwrite the closed
hierarchical choice or test files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.empirical import (  # noqa: E402
    HOLDOUT_CUTOFF,
    MIN_BUCKET_CASES,
    SIZE_BUCKET_EDGES,
    RatioQuantileModel,
    load_sip_tasks,
)
from parallax.evaluation.benchmark import standardized_accuracy, wilcoxon_signed_rank  # noqa: E402

PROTOCOL_PATH = ROOT / "datasets" / "eval" / "sip_correction_protocol_v1.json"
CHOICE = ROOT / "datasets" / "eval" / "sip_correction_choice.json"
RESULT = ROOT / "datasets" / "eval" / "sip_correction_test.json"
JOURNAL = ROOT / "datasets" / "eval" / "journal.jsonl"
VALIDATION_START = date(2010, 1, 1)
IMPLEMENTED_KINDS = frozenset({"recent-window", "shrink-quantile", "round-by-bucket", "size-buckets"})
FORBIDDEN_NAMES = frozenset({"sip_model_choice.json", "sip_model_test.json"})
PROBS = (0.1, 0.5, 0.9)


def load_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def protocol_sha256() -> str:
    return hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()


def require_protocol(protocol: dict) -> None:
    if protocol.get("id") != "sip_correction_protocol_v1":
        raise SystemExit("unexpected protocol id")
    if date.fromisoformat(protocol["validation_start"]) != VALIDATION_START:
        raise SystemExit("validation start drifted")
    if date.fromisoformat(protocol["holdout_start"]) != HOLDOUT_CUTOFF:
        raise SystemExit("holdout start drifted")
    if tuple(protocol["shipped_edges"]) != tuple(SIZE_BUCKET_EDGES):
        raise SystemExit("shipped edges drifted")
    if protocol["min_cases"] != MIN_BUCKET_CASES:
        raise SystemExit("min_cases drifted")
    if list(protocol["probs"]) != list(PROBS):
        raise SystemExit("quantiles drifted")
    boot = protocol["bootstrap"]
    if boot["draws"] != 5000 or boot["seed"] != 20261017:
        raise SystemExit("bootstrap settings drifted")
    if protocol["min_coverage"] != 75:
        raise SystemExit("coverage gate drifted")
    ids = [c["id"] for c in protocol["candidates"]]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate candidate id")
    for spec in protocol["candidates"]:
        if spec["kind"] not in IMPLEMENTED_KINDS:
            raise SystemExit(f"unknown kind {spec['kind']}")


def split_for_select(tasks):
    train = [t for t in tasks if t.estimated_on < VALIDATION_START]
    val = [t for t in tasks if VALIDATION_START <= t.estimated_on < HOLDOUT_CUTOFF]
    return train, val


def split_for_test(tasks):
    train = [t for t in tasks if t.estimated_on < HOLDOUT_CUTOFF]
    test = [t for t in tasks if t.estimated_on >= HOLDOUT_CUTOFF]
    return train, test


def _ratios_by_bucket(pairs, edges):
    by: dict[int, list[float]] = defaultdict(list)
    pooled: list[float] = []
    edges_t = tuple(edges)
    for est, act in pairs:
        ratio = act / est
        by[bisect_right(edges_t, est)].append(ratio)
        pooled.append(ratio)
    return {b: np.asarray(v, dtype=float) for b, v in by.items()}, np.asarray(pooled, dtype=float)


def _from_ratios(estimate: float, ratios) -> list[float]:
    q = np.quantile(np.asarray(ratios, dtype=float), PROBS)
    return [float(estimate * x) for x in q]


def _bucket_or_pooled(by, pooled, bucket: int, min_cases: int):
    ratios = by.get(bucket)
    if ratios is not None and len(ratios) >= min_cases:
        return ratios
    return pooled


def size_only_predictor(train):
    model = RatioQuantileModel.fit([(t.estimate_hours, t.actual_hours) for t in train])

    def predict(task):
        return [float(x) for x in model.predict(task.estimate_hours)]

    return predict


def fit_recent(train, start: date, min_cases: int):
    window = [t for t in train if t.estimated_on >= start]
    if len(window) < min_cases:
        raise ValueError(f"window {start.isoformat()} has {len(window)} rows")
    return size_only_predictor(window)


def fit_shrink(train, k: float, edges, min_cases: int):
    by, pooled = _ratios_by_bucket([(t.estimate_hours, t.actual_hours) for t in train], edges)
    if len(pooled) < min_cases:
        raise ValueError(f"shrink fit has {len(pooled)} rows")
    edges_t = tuple(edges)
    qp = np.quantile(pooled, PROBS)

    def predict(task):
        bucket = by.get(bisect_right(edges_t, task.estimate_hours))
        n = 0 if bucket is None else len(bucket)
        if n == 0:
            q = qp
        else:
            qb = np.quantile(bucket, PROBS)
            w = n / (n + k)
            q = w * qb + (1.0 - w) * qp
        return [float(task.estimate_hours * x) for x in q]

    return predict


def fit_round(train, edges, min_cases: int, round_hours):
    round_set = set(round_hours)
    edges_t = tuple(edges)
    by_all: dict[int, list[float]] = defaultdict(list)
    by_kind: dict[tuple[str, int], list[float]] = defaultdict(list)
    pooled: list[float] = []
    for task in train:
        ratio = task.actual_hours / task.estimate_hours
        bucket = bisect_right(edges_t, task.estimate_hours)
        kind = "round" if task.estimate_hours in round_set else "odd"
        by_all[bucket].append(ratio)
        by_kind[(kind, bucket)].append(ratio)
        pooled.append(ratio)
    pooled_a = np.asarray(pooled, dtype=float)
    by_all_a = {b: np.asarray(v, dtype=float) for b, v in by_all.items()}
    by_kind_a = {key: np.asarray(v, dtype=float) for key, v in by_kind.items()}

    def predict(task):
        bucket = bisect_right(edges_t, task.estimate_hours)
        kind = "round" if task.estimate_hours in round_set else "odd"
        subset = by_kind_a.get((kind, bucket))
        if subset is not None and len(subset) >= min_cases:
            use = subset
        else:
            use = _bucket_or_pooled(by_all_a, pooled_a, bucket, min_cases)
        return _from_ratios(task.estimate_hours, use)

    return predict


def fit_size_buckets(train, edges, min_cases: int):
    by, pooled = _ratios_by_bucket([(t.estimate_hours, t.actual_hours) for t in train], edges)
    if len(pooled) < min_cases:
        raise ValueError(f"bucket fit has {len(pooled)} rows")
    edges_t = tuple(edges)

    def predict(task):
        bucket = bisect_right(edges_t, task.estimate_hours)
        return _from_ratios(task.estimate_hours, _bucket_or_pooled(by, pooled, bucket, min_cases))

    return predict


def fit_predictor(spec: dict, train, protocol: dict):
    min_cases = protocol["min_cases"]
    edges = protocol["shipped_edges"]
    kind = spec["kind"]
    if kind == "recent-window":
        return fit_recent(train, date.fromisoformat(spec["start"]), min_cases)
    if kind == "shrink-quantile":
        return fit_shrink(train, float(spec["k"]), edges, min_cases)
    if kind == "round-by-bucket":
        return fit_round(train, edges, min_cases, protocol["round_hours"])
    if kind == "size-buckets":
        return fit_size_buckets(train, spec["edges"], min_cases)
    raise ValueError(kind)


def score_tasks(tasks, predict, human: bool = False) -> tuple[dict, np.ndarray]:
    actual = np.array([t.actual_hours for t in tasks], dtype=float)
    if human:
        p50 = np.array([t.estimate_hours for t in tasks], dtype=float)
        err = np.abs(actual - p50)
        metrics = {
            "n": len(tasks),
            "mae": float(err.mean()),
            "mdae": float(np.median(err)),
            "sa": float(standardized_accuracy(actual, p50)),
            "pred_25": float(np.mean(err / actual <= 0.25) * 100),
            "mdape": float(np.median(err / actual) * 100),
            "coverage_p10_p90": None,
            "mean_width": None,
        }
        return metrics, err
    rows = [predict(t) for t in tasks]
    p10 = np.array([r[0] for r in rows], dtype=float)
    p50 = np.array([r[1] for r in rows], dtype=float)
    p90 = np.array([r[2] for r in rows], dtype=float)
    err = np.abs(actual - p50)
    metrics = {
        "n": len(tasks),
        "mae": float(err.mean()),
        "mdae": float(np.median(err)),
        "sa": float(standardized_accuracy(actual, p50)),
        "pred_25": float(np.mean(err / actual <= 0.25) * 100),
        "mdape": float(np.median(err / actual) * 100),
        "coverage_p10_p90": float(np.mean((p10 <= actual) & (actual <= p90)) * 100),
        "mean_width": float(np.mean(p90 - p10)),
    }
    return metrics, err


def mae_gain_ci(err_base: np.ndarray, err_new: np.ndarray, draws: int, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(err_base)
    gains = np.empty(draws)
    for i in range(draws):
        idx = rng.integers(0, n, n)
        gains[i] = float(err_base[idx].mean() - err_new[idx].mean())
    lo, hi = np.quantile(gains, [0.025, 0.975])
    return float(lo), float(hi)


def decide_promotion(candidates, size_only_mae: float, min_coverage: float):
    eligible = []
    for index, row in enumerate(candidates):
        coverage = row["coverage_p10_p90"]
        if coverage is None:
            continue
        if coverage >= min_coverage and row["mae"] < size_only_mae and row["ci_low"] > 0:
            eligible.append((row["mae"], index, row["id"]))
    if not eligible:
        return None
    eligible.sort()
    return eligible[0][2]


def _p_value(err_a, err_b):
    w = wilcoxon_signed_rank(err_a, err_b)
    if w["p_value"] is None:
        return None
    return float(f"{w['p_value']:.3g}")


def evaluate_validation(train, val, protocol: dict) -> dict:
    require_protocol(protocol)
    for task in list(train) + list(val):
        if task.estimated_on >= HOLDOUT_CUTOFF:
            raise RuntimeError(f"holdout task in selection: {task.task_id}")
    human_metrics, human_err = score_tasks(val, None, human=True)
    base_metrics, base_err = score_tasks(val, size_only_predictor(train))
    draws = protocol["bootstrap"]["draws"]
    seed = protocol["bootstrap"]["seed"]
    rows = []
    for spec in protocol["candidates"]:
        metrics, err = score_tasks(val, fit_predictor(spec, train, protocol))
        lo, hi = mae_gain_ci(base_err, err, draws, seed)
        rows.append({
            "id": spec["id"],
            "kind": spec["kind"],
            **metrics,
            "ci_low": lo,
            "ci_high": hi,
            "wilcoxon_vs_human_p": _p_value(human_err, err),
            "wilcoxon_vs_size_only_p": _p_value(base_err, err),
        })
    promoted = decide_promotion(rows, base_metrics["mae"], protocol["min_coverage"])
    return {"human": human_metrics, "size_only": base_metrics, "candidates": rows, "promoted": promoted}


def integrity_ok(payload: dict, protocol: dict) -> bool:
    expected = protocol["integrity_check"]
    got_n = payload["size_only"]["n"]
    got_mae = f"{round(payload['size_only']['mae'], 3):.3f}"
    got_human = f"{round(payload['human']['mae'], 3):.3f}"
    return (
        got_n == expected["n_validation"]
        and got_mae == f"{float(expected['size_only_mae_rounded_3dp']):.3f}"
        and got_human == f"{float(expected['human_mae_rounded_3dp']):.3f}"
    )


def lowest_mae_row(candidates) -> dict:
    return min(enumerate(candidates), key=lambda item: (item[1]["mae"], item[0]))[1]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def git_head() -> str:
    return _git("rev-parse", "HEAD").strip()


def tracked_dirty() -> str:
    return _git("status", "--porcelain", "--untracked-files=no")


def committed_and_clean(path: Path) -> bool:
    rel = path.resolve().relative_to(ROOT).as_posix()
    listed = _git("ls-files", "--", rel).strip()
    dirty = _git("status", "--porcelain", "--", rel).strip()
    return bool(listed) and not dirty


def choice_committed(path: Path) -> bool:
    return committed_and_clean(path)


def assert_safe_output(path: Path) -> None:
    if path.name in FORBIDDEN_NAMES:
        raise SystemExit("refusing to write a closed hierarchical result")
    try:
        rel = path.resolve().relative_to(ROOT)
    except ValueError:
        return
    if rel.parts[:1] == ("apps",):
        raise SystemExit("refusing to write under apps")


def write_json(path: Path, payload: dict) -> None:
    assert_safe_output(path)
    path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")


def journal_has(path: Path, tag: str) -> bool:
    if not path.exists():
        return False
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip() and json.loads(line).get("tag") == tag:
                return True
    return False


def append_journal(path: Path, entry: dict) -> None:
    assert_safe_output(path)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _summary_row(reader: str, metrics: dict, wilcoxon_p=None) -> dict:
    row = {
        "reader": reader,
        "n": metrics["n"],
        "mae": round(metrics["mae"], 3),
        "pred_25": round(metrics["pred_25"], 2),
        "sa": round(metrics["sa"], 2),
        "coverage_p10_p90": None if metrics["coverage_p10_p90"] is None else round(metrics["coverage_p10_p90"], 2),
    }
    if wilcoxon_p is not None:
        row["wilcoxon_vs_human_p"] = wilcoxon_p
    return row


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes")


def validation_note(payload: dict) -> str:
    best = lowest_mae_row(payload["candidates"])
    ci = [round(best["ci_low"], 3), round(best["ci_high"], 3)]
    base = round(payload["size_only"]["mae"], 3)
    if payload["promoted"] is None:
        return (
            f"No correction promoted on 2010. Lowest MAE was {best['id']} "
            f"{round(best['mae'], 3)} h vs size-only {base} h, "
            f"coverage {round(best['coverage_p10_p90'], 2)}%, MAE-gain 95% CI {ci}. "
            f"2011-2014 was not scored."
        )
    return f"Promoted {payload['promoted']} on 2010. select does not score 2011-2014."


def cmd_select(args) -> int:
    choice_path = Path(args.choice)
    journal_path = Path(args.journal)
    assert_safe_output(choice_path)
    if choice_path.exists():
        print("choice file already exists; refusing a second selection")
        return 2
    if journal_has(journal_path, "sip_correction_validation") or journal_has(journal_path, "sip_correction_holdout"):
        print("journal already records this protocol; refusing")
        return 2
    if not committed_and_clean(PROTOCOL_PATH) or not committed_and_clean(Path(__file__).resolve()):
        print("commit the protocol and this script before selecting")
        return 2
    dirty = tracked_dirty()
    if dirty.strip():
        print("tracked files differ from HEAD; commit the protocol before selecting")
        print(dirty)
        return 2
    protocol = load_protocol()
    train, val = split_for_select(load_sip_tasks())
    payload = evaluate_validation(train, val, protocol)
    if not integrity_ok(payload, protocol):
        size = payload["size_only"]
        human = payload["human"]
        print(
            "integrity check failed: "
            f"n={size['n']} size-only MAE {size['mae']:.3f} human MAE {human['mae']:.3f}"
        )
        return 1
    choice = {
        "protocol": protocol["id"],
        "protocol_sha256": protocol_sha256(),
        "git_head": git_head(),
        "promoted": payload["promoted"],
        "validation": "fit estimated_on < 2010-01-01, score 2010 only",
        "holdout_scored": False,
        "rule": protocol["promotion"],
        "human": payload["human"],
        "size_only": payload["size_only"],
        "candidates": payload["candidates"],
    }
    write_json(choice_path, choice)
    note = validation_note(payload)
    if payload["promoted"] is None and not args.no_journal:
        best = lowest_mae_row(payload["candidates"])
        append_journal(journal_path, {
            "date": _now(),
            "tag": "sip_correction_validation",
            "labels": "SiP tasks estimated in 2010",
            "rules_version": "sip_correction_protocol_v1",
            "model": None,
            "summary": [
                _summary_row("human", payload["human"]),
                _summary_row("size-only", payload["size_only"]),
                _summary_row(best["id"], best, best["wilcoxon_vs_human_p"]),
            ],
            "note": note,
        })
    print(f"{'model':22} {'MAE':8} {'cov':8} {'ci_low':8} {'ci_high':8}")
    print(f"{'human':22} {payload['human']['mae']:8.3f}")
    print(f"{'size-only':22} {payload['size_only']['mae']:8.3f} {payload['size_only']['coverage_p10_p90']:8.2f}")
    for row in payload["candidates"]:
        print(f"{row['id']:22} {row['mae']:8.3f} {row['coverage_p10_p90']:8.2f} {row['ci_low']:8.3f} {row['ci_high']:8.3f}")
    print(note)
    return 0


def cmd_test(args) -> int:
    choice_path = Path(args.choice)
    result_path = Path(args.result)
    journal_path = Path(args.journal)
    choice = json.loads(choice_path.read_text(encoding="utf-8"))
    protocol = load_protocol()
    require_protocol(protocol)
    if choice.get("protocol_sha256") != protocol_sha256():
        print("protocol hash mismatch; refusing")
        return 2
    if not choice.get("promoted"):
        print("no candidate was promoted; refusing to score 2011-2014")
        return 2
    recomputed = decide_promotion(choice["candidates"], choice["size_only"]["mae"], protocol["min_coverage"])
    if recomputed != choice["promoted"]:
        print("promoted id does not match the stored 2010 metrics; refusing")
        return 2
    if not choice_committed(choice_path):
        print("commit the choice file before test")
        return 2
    dirty = tracked_dirty()
    if dirty.strip():
        print("tracked files differ from HEAD; refusing")
        print(dirty)
        return 2
    if result_path.exists():
        print("result file already exists; refusing a second test")
        return 2
    if journal_has(journal_path, "sip_correction_holdout"):
        print("holdout journal line already exists; refusing")
        return 2
    spec = next(c for c in protocol["candidates"] if c["id"] == choice["promoted"])
    train, test = split_for_test(load_sip_tasks())
    human_metrics, human_err = score_tasks(test, None, human=True)
    base_metrics, base_err = score_tasks(test, size_only_predictor(train))
    cand_metrics, cand_err = score_tasks(test, fit_predictor(spec, train, protocol))
    lo, hi = mae_gain_ci(base_err, cand_err, protocol["bootstrap"]["draws"], protocol["bootstrap"]["seed"])
    ship = (
        cand_metrics["mae"] < base_metrics["mae"]
        and cand_metrics["coverage_p10_p90"] >= protocol["min_coverage"]
        and lo > 0
    )
    report = {
        "protocol": protocol["id"],
        "protocol_sha256": protocol_sha256(),
        "promoted": choice["promoted"],
        "train": f"estimated before {HOLDOUT_CUTOFF.isoformat()} ({len(train)})",
        "test_n": len(test),
        "human": human_metrics,
        "size_only": base_metrics,
        "candidate": cand_metrics,
        "wilcoxon_vs_human_p": _p_value(human_err, cand_err),
        "wilcoxon_vs_size_only_p": _p_value(base_err, cand_err),
        "mae_gain_vs_size_only_95ci": [lo, hi],
        "ship_eligible": ship,
        "application_modified": False,
    }
    write_json(result_path, report)
    ci = [round(lo, 3), round(hi, 3)]
    note = (
        f"{choice['promoted']} promoted on 2010, refit before 2011, scored once on 2011-2014. "
        f"MAE {cand_metrics['mae']:.3f} vs size-only {base_metrics['mae']:.3f}, "
        f"gain CI {ci}, ship_eligible {str(ship).lower()}. Application code was not changed."
    )
    if not args.no_journal:
        append_journal(journal_path, {
            "date": _now(),
            "tag": "sip_correction_holdout",
            "labels": "SiP 2011-2014",
            "rules_version": "sip_correction_protocol_v1",
            "model": None,
            "summary": [
                _summary_row("human", human_metrics),
                _summary_row("size-only", base_metrics),
                _summary_row(choice["promoted"], cand_metrics, report["wilcoxon_vs_human_p"]),
            ],
            "note": note,
        })
    print(note)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["select", "test"])
    parser.add_argument("--no-journal", action="store_true")
    parser.add_argument("--choice", type=Path, default=CHOICE)
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--journal", type=Path, default=JOURNAL)
    args = parser.parse_args(argv)
    return {"select": cmd_select, "test": cmd_test}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
