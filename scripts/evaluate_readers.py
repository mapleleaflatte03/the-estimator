"""Compare scope readers on the held-out clause set (datasets/eval/clause_labels_v1.json).

Readers:
  rules  - the regex taxonomy in parallax.extractor (Vietnamese/English, diacritics optional)
  jev    - Jev's single best kind + calibrated "tentative" probability
  hybrid - what the app ships: rules plus Jev's kind when Jev is confident,
           tentative if either reader says so

Usage:
  python scripts/evaluate_readers.py --labels datasets/eval/clause_labels_v2.json --tag round2 --note "..."
Needs JEVSTATION_API_KEY or TYPESAFE_API_KEY for clauses not yet in datasets/jev_cache/ (cached ones are free);
--rules-only never calls the API. Every run is appended to datasets/eval/journal.jsonl.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.extractor import _HEDGES, _match_components, fold  # noqa: E402
from parallax.extractor import proposed_kinds  # noqa: E402
from parallax.jev import (  # noqa: E402
    KIND_CONFIDENCE_MIN, KIND_Q, KIND_TO_COMPONENT, SHIPPED_CACHE, TENTATIVE_MIN, TENTATIVE_Q, VERIFY_MIN, JevReader,
    load_dotenv,
)

COMPONENT_TO_KIND = {v: k for k, v in KIND_TO_COMPONENT.items() if v}
COMPONENT_TO_KIND.update({"audit": "permissions_audit", "security": "permissions_audit", "migration": "data_import",
                          "rag": "ai_assistant"})


def rules_reading(text: str) -> tuple[set[str], bool]:
    kinds = {COMPONENT_TO_KIND[c.key] for c in _match_components(text) if c.key in COMPONENT_TO_KIND}
    return kinds, bool(_HEDGES.search(fold(text)))


def shipped_rows(details):
    """What the app does: Jev's kind is used only when rules found nothing; otherwise it is asked as a question."""
    rows, suggested_primary = [], 0
    for d in details:
        expected = set(d["expected"])
        r = set(d["rules"])
        j = d["jev"] if d["jev"] != "other" and d["jev_confidence"] >= KIND_CONFIDENCE_MIN else None
        pred = r if r else ({j} if j else set())
        if j and r and j not in r and d["expected"][0] == j and d["expected"][0] not in r:
            suggested_primary += 1
        rows.append((pred, expected, d["expected"], d["rules_tentative"] or d["jev_tentative"] >= TENTATIVE_MIN, d["tentative"]))
    return rows, suggested_primary


def summarise(details, rows_by_reader):
    summary = [score(k, v) for k, v in rows_by_reader.items()]
    rows, suggested = shipped_rows(details)
    shipped = score("shipped", rows)
    shipped["primary_kind_suggested_as_question"] = suggested
    out = summary + [shipped]
    if any("verify" in d for d in details):
        vrows, vsuggested = shipped_rows([{**d, "rules": d["rules_verified"]} for d in details])
        verified = score("shipped+verify", vrows)
        verified["primary_kind_suggested_as_question"] = vsuggested
        out.append(verified)
    return out


def verified_rules(rules: set[str], d: dict) -> list[str]:
    """Rule kinds Jev confirmed (VERIFY_MIN); mirrors the extractor, including its keep-all fallback."""
    own = d["jev"] if d["jev"] != "other" and d["jev_confidence"] >= KIND_CONFIDENCE_MIN else None
    kept = [k for k in rules if k == own or d["verify"].get(k, 1.0) >= VERIFY_MIN]
    return sorted(kept if kept or own else rules)


def score(name, rows):
    n = len(rows)
    hits = sum(len(p & e) for p, e, *_ in rows)
    predicted = sum(len(p) for p, *_ in rows)
    expected = sum(len(e) for _, e, *_ in rows)
    primary = sum(e_list[0] in p for p, _, e_list, *_ in rows)
    tentative_ok = sum(t_pred == t_true for *_, t_pred, t_true in rows)
    tp = sum(t_pred and t_true for *_, t_pred, t_true in rows)
    tentative_total = sum(t_true for *_, t_true in rows)
    false_tentative = sum(t_pred and not t_true for *_, t_pred, t_true in rows)
    return {
        "reader": name,
        "n_clauses": n,
        "primary_kind_found": primary,
        "kind_recall_pct": round(hits / expected * 100, 1),
        "kind_precision_pct": round(hits / predicted * 100, 1) if predicted else 0.0,
        "tentative_correct": tentative_ok,
        "tentative_caught": f"{tp}/{tentative_total}",
        "false_tentative": false_tentative,
    }


def rules_version() -> str:
    """Fingerprint of the rule reader, so journal entries show which rules produced a result."""
    import parallax.extractor as ex

    return hashlib.sha256(Path(ex.__file__).read_bytes()).hexdigest()[:10]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="datasets/eval/clause_labels_v1.json")
    ap.add_argument("--tag", default="latest")
    ap.add_argument("--note", default="")
    ap.add_argument("--rules-only", action="store_true")
    ap.add_argument("--verify", action="store_true", help="also score the shipped reader with AI verification of rule kinds")
    ap.add_argument("--allow-partial", action="store_true",
                    help="score only the clauses Jev could read (e.g. credits ran out) and record how many were unread")
    args = ap.parse_args()
    labels_path = ROOT / args.labels
    labels = json.loads(labels_path.read_text(encoding="utf-8"))["clauses"]
    load_dotenv()
    # Only the two judged questions are scored here; the overrun question is validated on SiP outcomes.
    reader = JevReader(cache_path=SHIPPED_CACHE, questions=(KIND_Q, TENTATIVE_Q), max_calls_per_hour=None)
    if args.rules_only:
        reader.keys = []
    cached_before = sum(reader.cached(c["text"]) is not None for c in labels)
    readings = reader.read([c["text"] for c in labels])
    if args.rules_only:
        return rules_only_report(args, labels)
    unread = [c["text"] for c in labels if c["text"] not in readings]
    if unread and not args.allow_partial:
        for text in unread:
            print(f"!! no Jev reading for: {text}", file=sys.stderr)
        return 1
    labels = [c for c in labels if c["text"] in readings]
    if not labels:
        print("!! Jev read nothing:", reader.status(), file=sys.stderr)
        return 1
    if args.verify:
        reader.verify(readings, {t: proposed_kinds(t) for t in readings})
    rows = {"rules": [], "jev": [], "hybrid": []}
    details = []
    for c in labels:
        expected = set(c["kinds"])
        r_kinds, r_tent = rules_reading(c["text"])
        j = readings[c["text"]]
        j_kinds = set() if j.kind == "other" else {j.kind}
        h_kinds = set(r_kinds)
        if j.kind != "other" and j.kind_confidence >= KIND_CONFIDENCE_MIN:
            h_kinds.add(j.kind)
        rows["rules"].append((r_kinds, expected, c["kinds"], r_tent, c["tentative"]))
        rows["jev"].append((j_kinds, expected, c["kinds"], j.tentative >= 0.5, c["tentative"]))
        rows["hybrid"].append((h_kinds, expected, c["kinds"], r_tent or j.tentative >= TENTATIVE_MIN, c["tentative"]))
        details.append({"text": c["text"], "expected": c["kinds"], "tentative": c["tentative"],
                        "rules": sorted(r_kinds), "rules_tentative": r_tent,
                        "jev": j.kind, "jev_confidence": j.kind_confidence, "jev_tentative": j.tentative})
        if args.verify:
            details[-1]["verify"] = {k[len("needs_"):]: v for k, v in j.extra.items() if k.startswith("needs_")}
            details[-1]["rules_verified"] = verified_rules(r_kinds, details[-1])
    results = {
        "labels": args.labels,
        "tag": args.tag,
        "rules_version": rules_version(),
        "model": next(iter(readings.values())).model,
        "thresholds": {"kind_confidence_min": KIND_CONFIDENCE_MIN, "tentative_min": TENTATIVE_MIN},
        "summary": summarise(details, rows),
        "coverage": {
            "clauses_labelled": len(labels) + len(unread),
            "clauses_scored": len(labels),
            "unread": unread,
            "cached_before_run": cached_before,
            "fresh_api_calls": reader.calls_made,
            "credits_remaining_after": reader.credits_remaining,
        },
        "details": details,
    }
    out = ROOT / "datasets" / "eval" / f"reader_results_{args.tag}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    journal(args, results["summary"], results["model"], results["coverage"])
    for s in results["summary"]:
        print(s)
    print("Jev status:", reader.status())
    return 0


def journal(args, summary, model, coverage=None) -> None:
    entry = {
        "date": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="minutes"),
        "tag": args.tag,
        "labels": args.labels,
        "rules_version": rules_version(),
        "model": model,
        "summary": summary,
        "note": args.note,
    }
    if coverage:
        entry["coverage"] = {k: v for k, v in coverage.items() if k != "unread"}
    with open(ROOT / "datasets" / "eval" / "journal.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def rules_only_report(args, labels) -> int:
    rows = []
    for c in labels:
        r_kinds, r_tent = rules_reading(c["text"])
        rows.append((r_kinds, set(c["kinds"]), c["kinds"], r_tent, c["tentative"]))
    summary = [score("rules", rows)]
    journal(args, summary, None)
    print(summary[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
