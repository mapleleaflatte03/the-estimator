"""Dev experiment: let Jev verify each kind of work the keyword rules propose for a clause.

For every rule-matched kind that is not Jev's own top kind, Jev answers a yes/no question:
"Does the requirement itself ask for <kind description>?". Kinds below a threshold are dropped.
Run on rounds 1-6 (all already used: this is DEV, for choosing the threshold). The chosen
setting must then be confirmed once on a fresh, pre-labelled round.
Usage: python scripts/verify_kinds_dev.py [--rounds 1 2 4 5 6] [--labels path]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_readers import rules_reading  # noqa: E402
from parallax.jev import KIND_CONFIDENCE_MIN, KINDS, SHIPPED_ANSWERS, JevReader, load_dotenv, verify_question  # noqa: E402


def score(rows):
    hits = sum(len(p & e) for p, e, _ in rows)
    pred = sum(len(p) for p, _, _ in rows)
    exp = sum(len(e) for _, e, _ in rows)
    primary = sum(first in p for p, _, first in rows)
    return {"precision": round(hits / pred * 100, 1) if pred else 0, "recall": round(hits / exp * 100, 1),
            "primary": f"{primary}/{len(rows)}", "predicted_kinds": pred}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", nargs="*", default=["1", "2", "3", "4", "5", "6"])
    ap.add_argument("--labels")
    args = ap.parse_args()
    load_dotenv()
    paths = [ROOT / args.labels] if args.labels else [ROOT / "datasets" / "eval" / f"clause_labels_v{r}.json" for r in args.rounds]
    clauses = [c for p in paths for c in json.loads(p.read_text(encoding="utf-8"))["clauses"]]
    reader = JevReader(cache_path=SHIPPED_ANSWERS, max_calls_per_hour=None)
    readings = reader.read([c["text"] for c in clauses])
    pairs = []
    for c in clauses:
        r_kinds, _ = rules_reading(c["text"])
        j = readings.get(c["text"])
        for k in r_kinds:
            if j is None or k != j.kind:
                pairs.append((c["text"], k))
    qs = {k: verify_question(k) for k in KINDS if k != "other"}
    for k in {k for _, k in pairs}:
        reader.ask([t for t, kk in pairs if kk == k], [qs[k]])
    results = {}
    for th in (None, 0.2, 0.3, 0.4, 0.5, 0.6):
        rows = []
        for c in clauses:
            r_kinds, _ = rules_reading(c["text"])
            j = readings.get(c["text"])
            jk = j.kind if j and j.kind != "other" and j.kind_confidence >= KIND_CONFIDENCE_MIN else None
            kept = set()
            for k in r_kinds:
                if th is None or k == jk:
                    kept.add(k)
                    continue
                a = reader.answer(c["text"], qs[k])
                if a is None or a["answer"]["noul"] >= th:
                    kept.add(k)
            pred = kept if kept else ({jk} if jk else set())
            rows.append((pred, set(c["kinds"]), c["kinds"][0]))
        results["shipped (no verification)" if th is None else f"verify >= {th}"] = score(rows)
    for k, v in results.items():
        print(f"{k:28} {v}")
    print("usd spent:", reader.status()["usd_spent_this_process"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
