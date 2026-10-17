"""Render datasets/eval/journal.jsonl as a Markdown table inside docs/EVALUATION_LOG.md.

The table sits between the AUTO markers and is regenerated from the journal on every run, so the numbers in the
log can never drift from what the evaluation scripts recorded. Usage: python scripts/journal_report.py [--check]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "datasets" / "eval" / "journal.jsonl"
LOG = ROOT / "docs" / "EVALUATION_LOG.md"
START, END = "<!-- AUTO:journal:start -->", "<!-- AUTO:journal:end -->"


def result(entry: dict) -> str:
    first = entry["summary"][0]
    odd = first.get("test_odd_projects")
    if odd:
        return (f"odd projects: retention {odd['retention_pct']}%, performance recall {odd['performance_recall_pct']}%, "
                f"security recall {odd['security_recall_pct']}%, false tentative {odd['false_tentative']}")
    if "mae_change_pct" in first:
        return (f"MAE {first['baseline_mae']} → {first['calibrated_mae']} h ({first['mae_change_pct']}%), "
                f"P10–P90 coverage {first.get('interval_coverage')}%")
    if "retention_pct" in first:
        return f"retention {first['retention_pct']}%, false tentative {first['false_tentative']}"
    if "spearman_log_ratio" in first:
        return "<br>".join(f"{r['question']}: Spearman {r['spearman_log_ratio']}, AUC {r['auc_overrun_25pct']}"
                           for r in entry["summary"])
    if first.get("reader") == "human":
        return "<br>".join(f"{r['reader']}: MAE {r['mae']} h, PRED(25) {r['pred_25']}%, "
                           f"P10–P90 {r['coverage_p10_p90'] if r['coverage_p10_p90'] is not None else '—'}"
                           for r in entry["summary"])
    parts = []
    for r in entry["summary"]:
        if r["reader"] in ("rules", "jev", "shipped"):
            parts.append(f"{r['reader']}: kind {r['primary_kind_found']}/{r['n_clauses']}, "
                         f"tentative {r['tentative_caught']}, false {r['false_tentative']}")
    return "<br>".join(parts)


def table() -> str:
    rows = ["| # | Date (UTC+7) | Run | Rules | Model | Result | Note |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for i, line in enumerate(JOURNAL.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        e = json.loads(line)
        cov = e.get("coverage")
        note = e.get("note", "").replace("|", "\\|")
        if cov:
            note += (f" (scored {cov['clauses_scored']}/{cov['clauses_labelled']}, API calls {cov['fresh_api_calls']}, "
                     f"credits left {cov['credits_remaining_after']})")
        rows.append(f"| {i} | {e['date'][:16].replace('T', ' ')} | `{e['tag']}` | `{e.get('rules_version') or ''}` | "
                    f"{e.get('model') or '—'} | {result(e)} | {note} |")
    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if the log is out of date instead of writing it")
    args = ap.parse_args()
    text = LOG.read_text(encoding="utf-8")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    updated = f"{head}{START}\n{table()}\n{END}{tail}"
    if args.check:
        return 0 if updated == text else 1
    LOG.write_text(updated, encoding="utf-8")
    print(f"{LOG.relative_to(ROOT)}: {len(table().splitlines()) - 2} runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
