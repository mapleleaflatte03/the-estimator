"""Compare scope readers on the held-out clause set (datasets/eval/clause_labels_v1.json).

Readers:
  rules  - the regex taxonomy in parallax.extractor (Vietnamese/English, diacritics optional)
  jev    - Jev's single best kind + calibrated "tentative" probability
  hybrid - what the app ships: rules plus Jev's kind when Jev is confident,
           tentative if either reader says so

Usage: python scripts/evaluate_readers.py   (needs JEVSTATION_API_KEY or TYPESAFE_API_KEY
for clauses that are not yet in datasets/jev_cache/; cached clauses cost nothing).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.extractor import _HEDGES, _match_components, fold  # noqa: E402
from parallax.jev import KIND_CONFIDENCE_MIN, KIND_TO_COMPONENT, SHIPPED_CACHE, TENTATIVE_MIN, JevReader  # noqa: E402

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
    return summary + [shipped]


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


def main() -> int:
    labels = json.loads((ROOT / "datasets" / "eval" / "clause_labels_v1.json").read_text(encoding="utf-8"))["clauses"]
    reader = JevReader(cache_path=SHIPPED_CACHE)
    readings = reader.read([c["text"] for c in labels])
    rows = {"rules": [], "jev": [], "hybrid": []}
    details = []
    for c in labels:
        expected = set(c["kinds"])
        r_kinds, r_tent = rules_reading(c["text"])
        j = readings.get(c["text"])
        if j is None:
            print(f"!! no Jev reading for: {c['text']}", file=sys.stderr)
            return 1
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
    results = {
        "labels": "datasets/eval/clause_labels_v1.json",
        "model": next(iter(readings.values())).model,
        "thresholds": {"kind_confidence_min": KIND_CONFIDENCE_MIN, "tentative_min": TENTATIVE_MIN},
        "summary": summarise(details, rows),
        "details": details,
    }
    # The first (truly held-out) run is kept in reader_results_v1_heldout.json.
    out = ROOT / "datasets" / "eval" / "reader_results_latest.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for s in results["summary"]:
        print(s)
    print("Jev status:", reader.status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
