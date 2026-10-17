"""Story-point benchmark: can the AI reader size work from text as well as a deep model trained for it?

Data (cite): M. Choetkiertikul, H. K. Dam, T. Tran, T. Pham, A. Ghose, T. Menzies, "A Deep Learning Model for
Estimating Story Points", IEEE TSE 45(7):637-656, 2019, doi:10.1109/TSE.2018.2792473. 23,313 issues, 16
open-source projects; files from https://github.com/morakotch/datasets @ 133a5f5 (scripts/fetch_storypoints.py),
including the authors' chronological train/validation/test split (`<project>_3sets.txt`, 60/20/20).
Published comparison: Table 3 of the authors' preprint (same repository, preprint.pdf, p. 11): MAE of Deep-SE and
of the Mean and Median baselines on the test split of each project. A later replication (Tawosi, Moussa, Sarro,
"Deep Learning for Agile Effort Estimation: Have We Solved the Problem Yet?", IEEE TSE 2023, arXiv:2201.05401)
found Deep-SE not significantly better than simple baselines in most projects; GPT2SP results are excluded because
the same group found an evaluation bug in them.

Method (no model is trained on text):
  1. Jev reads each issue (title + first 1,500 characters of the description) and answers SIZE_Q, a 5-level
     "score" from trivial to very large. Zero-shot: the question never sees story points.
  2. Per project, the score is mapped to story points with a monotone step function learned on the TRAINING split
     only (median story points per score bin, made non-decreasing).
  3. Mapping variants are compared on the VALIDATION split; the one with the lowest mean validation MAE across the
     16 projects is used, once, on the TEST split.
Commands: prepare (write and commit the protocol) | read (ask Jev) | select | test
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.evaluation.benchmark import standardized_accuracy, wilcoxon_signed_rank  # noqa: E402
from parallax.jev import SIZE_Q, JevReader, load_dotenv  # noqa: E402

DATA = ROOT / "datasets" / "external" / "deepse"
PROTOCOL = ROOT / "datasets" / "eval" / "storypoint_protocol_v1.json"
READINGS = ROOT / "datasets" / "eval" / "storypoint_jev_scores.json"
CHOICE = ROOT / "datasets" / "eval" / "storypoint_choice.json"
RESULT = ROOT / "datasets" / "eval" / "storypoint_result.json"
CACHE = ROOT / "datasets" / "jev_cache" / "storypoint_answers.json"
DESC_CHARS = 1500
csv.field_size_limit(10**8)

# Table 3 of the authors' preprint (Choetkiertikul et al., doi:10.1109/TSE.2018.2792473): test-split MAE.
PUBLISHED = {
    "mesos": ("ME", 1.02, 1.64, 1.73), "usergrid": ("UG", 1.03, 1.48, 1.60), "appceleratorstudio": ("AS", 1.36, 2.08, 1.84),
    "aptanastudio": ("AP", 2.71, 3.15, 3.71), "titanium": ("TI", 1.97, 3.05, 2.47), "duracloud": ("DC", 0.68, 1.30, 0.73),
    "bamboo": ("BB", 0.74, 1.75, 1.32), "clover": ("CV", 2.11, 3.49, 2.84), "jirasoftware": ("JI", 1.38, 2.48, 2.93),
    "moodle": ("MD", 5.97, 10.90, 7.18), "datamanagement": ("DM", 3.77, 5.29, 4.82), "mule": ("MU", 2.18, 2.59, 2.69),
    "mulestudio": ("MS", 3.23, 3.34, 3.30), "springxd": ("XD", 1.63, 2.27, 2.07), "talenddataquality": ("TD", 2.97, 4.81, 3.87),
    "talendesb": ("TE", 0.64, 1.14, 1.16),
}
VARIANTS = {"level": None, "bins5": 5, "bins10": 10, "bins20": 20}


def text_of(row: dict) -> str:
    desc = (row.get("description") or "").strip()
    return f"Title: {(row.get('title') or '').strip()}\nDescription: {desc[:DESC_CHARS]}"


def load_project(name: str) -> list[dict]:
    with open(DATA / f"{name}.csv", encoding="utf-8", errors="replace", newline="") as f:
        rows = list(csv.DictReader(f))
    with open(DATA / f"{name}_3sets.txt", encoding="utf-8") as f:
        flags = [line.split() for line in f.read().splitlines()[1:] if line.strip()]
    assert len(flags) == len(rows), (name, len(flags), len(rows))
    out = []
    for r, fl in zip(rows, flags):
        split = "train" if fl[0] == "1" else "valid" if fl[1] == "1" else "test"
        out.append({"key": r["issuekey"], "text": text_of(r), "sp": float(r["storypoint"]), "split": split})
    return out


def fit_mapping(scores: np.ndarray, sps: np.ndarray, variant: str):
    bins = VARIANTS[variant]
    if bins is None:
        edges = np.array([0.5, 1.5, 2.5, 3.5])
    else:
        edges = np.unique(np.quantile(scores, np.linspace(0, 1, bins + 1)[1:-1]))
    idx = np.searchsorted(edges, scores, side="right")
    overall = float(np.median(sps))
    meds = []
    for b in range(len(edges) + 1):
        v = sps[idx == b]
        meds.append(float(np.median(v)) if len(v) else np.nan)
    # Fill empty bins from neighbours, then enforce a non-decreasing step function.
    meds = np.array(meds)
    for b in range(len(meds)):
        if np.isnan(meds[b]):
            left = meds[:b][~np.isnan(meds[:b])]
            meds[b] = left[-1] if len(left) else overall
    meds = np.maximum.accumulate(meds)
    return lambda s: meds[np.searchsorted(edges, s, side="right")]


def cmd_prepare(_args) -> int:
    projects = {p: load_project(p) for p in PUBLISHED}
    PROTOCOL.write_text(json.dumps({
        "dataset": "Choetkiertikul et al. 2019, doi:10.1109/TSE.2018.2792473; github.com/morakotch/datasets @ 133a5f5",
        "splits": "authors' chronological 60/20/20 split files (<project>_3sets.txt)",
        "n_issues": {p: len(v) for p, v in projects.items()},
        "question": {"tag": SIZE_Q.tag, "instructions": SIZE_Q.instructions, "levels": list(SIZE_Q.criteria)},
        "input": f"title + first {DESC_CHARS} characters of the description",
        "mapping_variants": list(VARIANTS),
        "selection": "lowest mean VALIDATION MAE over the 16 projects; then one run on TEST",
        "published_comparison": "Table 3 of the authors' preprint: Deep-SE, Mean, Median test MAE",
        "primary_metric": "test MAE per project vs Deep-SE (published) and vs Mean/Median computed on the same split",
    }, indent=1) + "\n", encoding="utf-8")
    print({p: len(v) for p, v in projects.items()}, sum(len(v) for v in projects.values()))
    return 0


def reader() -> JevReader:
    load_dotenv()
    return JevReader(cache_path=CACHE, max_calls_per_hour=None, questions=())


def cmd_read(args) -> int:
    r = reader()
    texts = [i["text"] for p in PUBLISHED for i in load_project(p)]
    todo = r.missing(texts, [SIZE_Q])
    print(f"{len(texts)} issues, {len(todo)} to read")
    r.ask(texts, [SIZE_Q], max_calls=args.max_calls, workers=6)
    data = {}
    for p in PUBLISHED:
        for i in load_project(p):
            a = r.answer(i["text"], SIZE_Q)
            if a is not None:
                data[f"{p}/{i['key']}"] = a["answer"]["score"]
    READINGS.write_text(json.dumps(data, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    st = r.status()
    print(f"scored {len(data)}/{len(texts)}; usd {st['usd_spent_this_process']}; last error {st['last_error']}; halted {st['halted']}")
    return 0


def scored(p: str, data: dict) -> list[dict]:
    return [{**i, "score": data[f"{p}/{i['key']}"]} for i in load_project(p) if f"{p}/{i['key']}" in data]


def cmd_select(_args) -> int:
    data = json.loads(READINGS.read_text(encoding="utf-8"))
    table = {v: {} for v in VARIANTS}
    for p in PUBLISHED:
        rows = scored(p, data)
        tr = [x for x in rows if x["split"] == "train"]
        va = [x for x in rows if x["split"] == "valid"]
        for v in VARIANTS:
            f = fit_mapping(np.array([x["score"] for x in tr]), np.array([x["sp"] for x in tr]), v)
            pred = f(np.array([x["score"] for x in va]))
            table[v][p] = round(float(np.mean(np.abs(pred - np.array([x["sp"] for x in va])))), 3)
    means = {v: round(float(np.mean(list(t.values()))), 4) for v, t in table.items()}
    best = min(means, key=means.get)
    CHOICE.write_text(json.dumps({"validation_mae": table, "mean": means, "chosen": best}, indent=1) + "\n", encoding="utf-8")
    print(means, "chosen:", best)
    return 0


def cmd_test(args) -> int:
    data = json.loads(READINGS.read_text(encoding="utf-8"))
    variant = json.loads(CHOICE.read_text(encoding="utf-8"))["chosen"]
    rows_out, spearman = [], []
    for p, (abbr, deepse, pub_mean, pub_median) in PUBLISHED.items():
        rows = scored(p, data)
        tr = [x for x in rows if x["split"] in ("train", "valid")]  # final model: fit on train + validation
        te = [x for x in rows if x["split"] == "test"]
        f = fit_mapping(np.array([x["score"] for x in tr]), np.array([x["sp"] for x in tr]), variant)
        y = np.array([x["sp"] for x in te])
        pred = f(np.array([x["score"] for x in te]))
        mean_pred = np.full(len(y), np.mean([x["sp"] for x in tr]))
        med_pred = np.full(len(y), np.median([x["sp"] for x in tr]))
        err, err_med = np.abs(pred - y), np.abs(med_pred - y)
        w = wilcoxon_signed_rank(err_med, err)
        s = np.array([x["score"] for x in te])
        rho = float(np.corrcoef(np.argsort(np.argsort(s)), np.argsort(np.argsort(y)))[0, 1])
        spearman.append(rho)
        rows_out.append({
            "project": abbr, "n_test": len(te), "mae": round(float(err.mean()), 2), "mdae": round(float(np.median(err)), 2),
            "sa": round(standardized_accuracy(y, pred), 1), "spearman_score_vs_sp": round(rho, 3),
            "mean_baseline_mae": round(float(np.abs(mean_pred - y).mean()), 2),
            "median_baseline_mae": round(float(err_med.mean()), 2),
            "wilcoxon_vs_median_p": float(f"{w['p_value']:.3g}") if w["p_value"] is not None else None,
            "deepse_published_mae": deepse, "published_mean_mae": pub_mean, "published_median_mae": pub_median,
        })
    beats = sum(r["mae"] < r["deepse_published_mae"] for r in rows_out)
    ties = sum(r["mae"] == r["deepse_published_mae"] for r in rows_out)
    beats_median = sum(r["mae"] < r["median_baseline_mae"] for r in rows_out)
    report = {
        "variant": variant, "projects": rows_out,
        "mean_mae": round(float(np.mean([r["mae"] for r in rows_out])), 3),
        "mean_deepse_mae": round(float(np.mean([r["deepse_published_mae"] for r in rows_out])), 3),
        "mean_median_baseline_mae": round(float(np.mean([r["median_baseline_mae"] for r in rows_out])), 3),
        "projects_better_than_deepse": beats, "projects_equal_to_deepse": ties,
        "projects_better_than_median": beats_median,
        "projects_significantly_better_than_median": sum(
            (r["wilcoxon_vs_median_p"] or 1) < 0.05 and r["mae"] < r["median_baseline_mae"] for r in rows_out),
        "median_spearman": round(float(np.median(spearman)), 3),
    }
    RESULT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    if not args.no_journal:
        entry = {"date": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes"),
                 "tag": "storypoint_benchmark", "labels": "Choetkiertikul et al. 2019 story points, 16 projects, test split",
                 "rules_version": None, "model": "jev-1.13.0",
                 "summary": [{"reader": "jev size score + per-project monotone map", "mae": report["mean_mae"],
                              "deepse_mae": report["mean_deepse_mae"], "median_mae": report["mean_median_baseline_mae"],
                              "better_than_deepse": f"{beats}/16", "better_than_median": f"{beats_median}/16"}],
                 "note": f"Zero-shot Jev size score (variant {variant} chosen on validation), test split once. "
                         f"Deep-SE MAE from the authors' preprint Table 3 (doi:10.1109/TSE.2018.2792473)."}
        with open(ROOT / "datasets" / "eval" / "journal.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "read", "select", "test"])
    ap.add_argument("--max-calls", type=int)
    ap.add_argument("--no-journal", action="store_true")
    args = ap.parse_args()
    return {"prepare": cmd_prepare, "read": cmd_read, "select": cmd_select, "test": cmd_test}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
