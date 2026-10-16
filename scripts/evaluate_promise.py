"""Rule-reader checks on PROMISE_exp: 969 real requirements from 49 projects, expert-labelled
(functional + 11 non-functional classes; Lima et al., SBES 2019, doi:10.1145/3350768.3350776).

The labels do not match our work kinds one-to-one, so only the honest overlaps are measured:
  retention     - share of requirements kept as requirements when pasted as plain sentences
  performance   - PE/SC requirements detected as performance work (recall) vs. false alarms elsewhere
  security      - SE requirements detected as security/permissions/auth work vs. false alarms elsewhere
  tentative     - false "not yet committed" flags (PROMISE requirements are firm "shall" statements)
The file is downloaded on first use into datasets/external/ (not committed). Free: no API calls.
Usage: python scripts/evaluate_promise.py --tag promise_rules --note "..."
"""
import argparse
import csv
import json
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_readers import rules_version  # noqa: E402
from parallax.extractor import _HEDGES, _match_components, extract_scope_and_wbs, fold  # noqa: E402

URL = ("https://raw.githubusercontent.com/AleksandarMitrevski/se-requirements-classification/"
       "HEAD/1-exploratory-analysis/data/PROMISE_exp.csv")
LOCAL = ROOT / "datasets" / "external" / "PROMISE_exp.csv"
SECURITY = {"security", "rbac", "auth", "audit"}


def load() -> list[dict]:
    if not LOCAL.exists():
        LOCAL.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, LOCAL)
    with open(LOCAL, encoding="utf-8", errors="replace", newline="") as f:
        return [{"text": " ".join(r["RequirementText"].split()), "cls": r["_class_"].strip(),
                 "project": int(r["ProjectID"])} for r in csv.DictReader(f)]


def pct(a, b):
    return round(a / b * 100, 1) if b else None


def measure(rows: list[dict]) -> dict:
    n = len(rows)
    by_project: dict[int, list[str]] = {}
    for r in rows:  # paste each project's requirements as plain prose (no bullets), as a client might
        by_project.setdefault(r["project"], []).append(r["text"].rstrip(".") + ".")
    kept = sum(
        sum(1 for req in extract_scope_and_wbs("promise", " ".join(texts)).requirements if req.req_id != "REQ-00")
        for texts in by_project.values()
    )
    perf_pos = [r for r in rows if r["cls"] in ("PE", "SC")]
    sec_pos = [r for r in rows if r["cls"] == "SE"]
    comps = {r["text"]: {c.key for c in _match_components(r["text"])} for r in rows}
    perf_hit = sum("performance" in comps[r["text"]] for r in perf_pos)
    perf_fp = sum("performance" in comps[r["text"]] for r in rows if r["cls"] not in ("PE", "SC"))
    sec_hit = sum(bool(comps[r["text"]] & SECURITY) for r in sec_pos)
    sec_fp = sum(bool(comps[r["text"]] & SECURITY) for r in rows if r["cls"] != "SE")
    tent = sum(bool(_HEDGES.search(fold(r["text"]))) for r in rows)
    return {
        "n_requirements": n,
        "retention_pct": pct(min(kept, n), n),
        "performance_recall_pct": pct(perf_hit, len(perf_pos)),
        "performance_false_alarms": f"{perf_fp}/{n - len(perf_pos)}",
        "security_recall_pct": pct(sec_hit, len(sec_pos)),
        "security_false_alarms": f"{sec_fp}/{n - len(sec_pos)}",
        "false_tentative": f"{tent}/{n}",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="promise_rules")
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    rows = load()
    # Split by project: even project ids are the "dev" half used to study errors and derive rule
    # fixes; odd ids are the "test" half whose misses are never inspected.
    summary = {
        "dev_even_projects": measure([r for r in rows if r["project"] % 2 == 0]),
        "test_odd_projects": measure([r for r in rows if r["project"] % 2 == 1]),
    }
    entry = {"date": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes"), "tag": args.tag,
             "labels": "PROMISE_exp (external)", "rules_version": rules_version(), "model": None,
             "summary": [{"reader": "rules", **summary}], "note": args.note}
    with open(ROOT / "datasets" / "eval" / "journal.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    (ROOT / "datasets" / "eval" / f"promise_results_{args.tag}.json").write_text(
        json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
