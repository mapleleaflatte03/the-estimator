"""Independent replication of the SiP finding on other companies' work (Itemlet, CC BY 4.0).

Question: does Jev's "would an experienced developer expect this to take longer than it
looks?" (OVERRUN_Q, chosen and thresholded on SiP only) still separate overrunning work
when applied, *unchanged*, to open-source Jira projects of other organisations?

Data: Itemlet (Abebe & Rusiecki 2026, doi:10.5281/zenodo.19411554, CC BY 4.0), Jira issues
with logged hours and `workratio` (= time spent / original estimate x 100), from which the
original estimate is recovered. Population: estimate >= 20 h (as in the SiP study), 400 h max.

Protocol, fixed before any Jev call (`prepare` writes it to datasets/eval/itemlet_protocol_v1.json):
  * random order of the population with a fixed seed; Jev reads issues in that order, so any
    prefix is a random sample (credits may run out part-way);
  * groups use the SiP training thresholds and factors exactly; nothing is fitted on Itemlet;
  * primary: median actual/estimate of the high group / low group; Spearman and AUC (>25% overrun);
  * secondary: MAE of estimate x SiP group factor vs the raw estimate (relative factors, so the
    team's overall bias is not corrected here).
Usage: python scripts/itemlet_jev_replication.py prepare|run|report [--max-calls N]
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
sys.path.insert(0, str(ROOT / "scripts"))

from parallax.jev import OVERRUN_Q, JevReader, load_dotenv  # noqa: E402
from parallax.risk import sip_prior  # noqa: E402
from sip_jev_study import auc, spearman  # noqa: E402

PARQUET = ROOT / "datasets" / "external" / "itemlet" / "itemlet_dataset.parquet"
URL = "https://zenodo.org/api/records/19411554/files/itemlet_dataset.parquet/content"
PROTOCOL = ROOT / "datasets" / "eval" / "itemlet_protocol_v1.json"
READINGS = ROOT / "datasets" / "eval" / "itemlet_jev_readings.json"
RESULT = ROOT / "datasets" / "eval" / "itemlet_replication.json"
CACHE = ROOT / "datasets" / "jev_cache" / "itemlet_answers.json"
SEED = 20261017
MIN_EST, MAX_EST = 20.0, 400.0


def load_population() -> list[dict]:
    import pandas as pd

    if not PARQUET.exists():
        PARQUET.parent.mkdir(parents=True, exist_ok=True)
        import urllib.request

        urllib.request.urlretrieve(URL, PARQUET)
    cols = ["issue_key", "issue_summary", "created", "workratio", "Total Time Logged (hours)", "project_key",
            "issuetype_name"]
    df = pd.read_parquet(PARQUET, columns=cols)
    df = df[(df.workratio > 0) & (df.workratio < 10**6) & (df["Total Time Logged (hours)"] > 0)].copy()
    df["actual"] = df["Total Time Logged (hours)"].astype(float)
    df["estimate"] = df["actual"] * 100.0 / df["workratio"].astype(float)
    df = df[(df.estimate >= MIN_EST) & (df.estimate <= MAX_EST)]
    df["summary"] = df.issue_summary.fillna("").str.strip()
    df = df[df.summary.str.len() >= 8].drop_duplicates("summary")
    return [{"key": r.issue_key, "summary": r.summary, "estimate": round(r.estimate, 3), "actual": r.actual,
             "project": r.project_key, "type": r.issuetype_name} for r in df.itertuples()]


def journal(tag, summary, note):
    entry = {"date": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes"), "tag": tag,
             "labels": "Itemlet Jira issues, estimate >= 20h (real actuals)", "rules_version": None,
             "model": "jev-1.13.0", "summary": summary, "note": note}
    with open(ROOT / "datasets" / "eval" / "journal.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_prepare(_args) -> int:
    pop = load_population()
    order = [p["key"] for p in pop]
    random.Random(SEED).shuffle(order)
    prior = sip_prior()
    PROTOCOL.write_text(json.dumps({
        "dataset": "Itemlet v1.0.0, doi:10.5281/zenodo.19411554, CC BY 4.0",
        "population": f"workratio > 0, logged hours > 0, {MIN_EST:g} <= estimate <= {MAX_EST:g} h, unique summaries",
        "n_population": len(pop),
        "question": OVERRUN_Q.tag,
        "sip_thresholds": list(prior.thresholds),
        "sip_factors": list(prior.factors),
        "primary": ["median actual/estimate high group / low group", "Spearman(p, log actual/estimate)",
                    "AUC for actual > 1.25 x estimate"],
        "secondary": ["MAE of estimate x SiP group factor vs raw estimate"],
        "seed": SEED,
        "order": order,
    }, indent=0) + "\n", encoding="utf-8")
    print(f"population {len(pop)} issues from {len({p['project'] for p in pop})} projects; protocol written")
    return 0


def reader() -> JevReader:
    load_dotenv()
    return JevReader(cache_path=CACHE, max_calls_per_hour=None, questions=())


def cmd_run(args) -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    by_key = {p["key"]: p for p in load_population()}
    order = [by_key[k] for k in protocol["order"] if k in by_key]
    r = reader()
    texts = [p["summary"] for p in order]
    todo = r.missing(texts, [OVERRUN_Q])
    # Ask strictly in protocol order so that whatever is read is a random prefix.
    todo_texts = [t for t, _ in todo][: (args.max_calls * 5 if args.max_calls else None)]
    r.ask(todo_texts, [OVERRUN_Q], workers=8)
    data = {}
    for p in order:
        a = r.answer(p["summary"], OVERRUN_Q)
        if a is None:
            break  # keep the prefix contiguous
        data[p["key"]] = a["answer"]["noul"]
    READINGS.write_text(json.dumps(data, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    print(f"read prefix {len(data)}/{len(order)}; charged {r.credits_charged}; known credits {r.credits_remaining}; "
          f"halted {r.halted}; last error {r.last_error}")
    return 0


def cmd_report(args) -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    by_key = {p["key"]: p for p in load_population()}
    data = json.loads(READINGS.read_text(encoding="utf-8"))
    rows = [(by_key[k], data[k]) for k in protocol["order"] if k in data and k in by_key]
    lo, hi = protocol["sip_thresholds"]
    factors = protocol["sip_factors"]

    def group(p):
        return int(p > lo) + int(p > hi)

    est = np.array([r["estimate"] for r, _ in rows])
    act = np.array([r["actual"] for r, _ in rows])
    p = np.array([q for _, q in rows])
    g = np.array([group(q) for q in p])
    ratio = act / est
    groups = []
    for k in range(3):
        idx = g == k
        groups.append({"group": k, "n": int(idx.sum()),
                       "ratio_p50": round(float(np.median(ratio[idx])), 3) if idx.any() else None,
                       "share_overrun_25pct": round(float(np.mean(ratio[idx] > 1.25)) * 100, 1) if idx.any() else None})
    adj = est * np.array([factors[k] for k in g])
    err_raw, err_adj = np.abs(act - est), np.abs(act - adj)
    rng = np.random.default_rng(SEED)
    diffs = [float(np.mean(err_raw[i]) - np.mean(err_adj[i]))
             for i in (rng.integers(0, len(rows), len(rows)) for _ in range(5000))]
    high_low = groups[2]["ratio_p50"] / groups[0]["ratio_p50"] if groups[0]["ratio_p50"] and groups[2]["ratio_p50"] else None
    report = {
        "n_read": len(rows), "n_population": protocol["n_population"],
        "projects": len({r["project"] for r, _ in rows}),
        "groups": groups,
        "high_vs_low_ratio_p50": round(high_low, 3) if high_low else None,
        "spearman": round(spearman(p, np.log(ratio)), 3),
        "auc_overrun_25pct": round(auc(list(p), list(ratio > 1.25)), 3),
        "mae_raw_estimate": round(float(err_raw.mean()), 2),
        "mae_with_sip_factors": round(float(err_adj.mean()), 2),
        "mae_gain_95ci": [round(float(x), 2) for x in np.quantile(diffs, [0.025, 0.975])],
        "mdae_raw": round(float(np.median(err_raw)), 2), "mdae_with_sip_factors": round(float(np.median(err_adj)), 2),
    }
    RESULT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not args.no_journal:
        journal(args.tag, [{"reader": "jev:overrun@v1 (SiP thresholds)", **{k: v for k, v in report.items() if k != "groups"}},
                           *[{"reader": f"group {x['group']}", **x} for x in groups]],
                f"Independent replication on Itemlet ({report['projects']} open-source Jira projects), SiP thresholds and factors unchanged, "
                f"protocol committed before the run. Read {len(rows)}/{protocol['n_population']} (random prefix).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "run", "report"])
    ap.add_argument("--max-calls", type=int)
    ap.add_argument("--tag", default="itemlet_replication")
    ap.add_argument("--no-journal", action="store_true")
    args = ap.parse_args()
    return {"prepare": cmd_prepare, "run": cmd_run, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
