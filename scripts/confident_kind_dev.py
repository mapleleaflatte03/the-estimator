"""Dev experiment: when Jev is very confident about a kind the rules missed, add it directly
(instead of only asking the user). Rounds 1-7 are all already used, so this is DEV for choosing
the threshold; the choice must be confirmed on a fresh round.
Usage: python scripts/confident_kind_dev.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_readers import rules_reading, verified_rules  # noqa: E402
from parallax.extractor import proposed_kinds  # noqa: E402
from parallax.jev import KIND_CONFIDENCE_MIN, KIND_Q, SHIPPED_ANSWERS, TENTATIVE_Q, JevReader, load_dotenv  # noqa: E402
from verify_kinds_dev import score  # noqa: E402


def main() -> int:
    load_dotenv()
    clauses = [c for r in range(1, 8)
               for c in json.loads((ROOT / "datasets" / "eval" / f"clause_labels_v{r}.json").read_text(encoding="utf-8"))["clauses"]]
    reader = JevReader(cache_path=SHIPPED_ANSWERS, max_calls_per_hour=None, questions=(KIND_Q, TENTATIVE_Q))
    readings = reader.read([c["text"] for c in clauses])
    reader.verify(readings, {t: proposed_kinds(t) for t in readings})
    for th in (None, 0.95, 0.9, 0.8, 0.7):
        rows = []
        for c in clauses:
            j = readings[c["text"]]
            r_kinds, _ = rules_reading(c["text"])
            d = {"jev": j.kind, "jev_confidence": j.kind_confidence,
                 "verify": {k[6:]: v for k, v in j.extra.items() if k.startswith("needs_")}}
            kept = set(verified_rules(r_kinds, d))
            jk = j.kind if j.kind != "other" and j.kind_confidence >= KIND_CONFIDENCE_MIN else None
            pred = kept if kept else ({jk} if jk else set())
            if th is not None and jk and j.kind_confidence >= th:
                pred = pred | {jk}
            rows.append((pred, set(c["kinds"]), c["kinds"][0]))
        print(f"{'shipped (verify)' if th is None else f'+ Jev kind if conf >= {th}':28}", score(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
