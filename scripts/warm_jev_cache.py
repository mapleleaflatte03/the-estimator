"""Pre-compute Jev answers for the sample briefs into datasets/jev_cache/ (shipped with the app).

Sample briefs then show AI readings on the live site without spending credits,
and every visitor gets the same, consistent result. Already-answered questions are free.
Usage: python scripts/warm_jev_cache.py [--dry-run] [--extra path/to/brief.txt ...]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.extractor import clause_texts, proposed_kinds  # noqa: E402
from parallax.jev import QUESTIONS_PER_CALL, SHIPPED_ANSWERS, JevReader, load_dotenv  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--extra", nargs="*", default=[])
    args = ap.parse_args()
    load_dotenv()
    reader = JevReader(cache_path=SHIPPED_ANSWERS, max_calls_per_hour=None)
    texts = []
    for path in sorted((ROOT / "datasets" / "golden_briefs").glob("*.json")):
        texts += clause_texts(json.loads(path.read_text(encoding="utf-8"))["brief_text"])
    for path in args.extra:
        texts += clause_texts(Path(path).read_text(encoding="utf-8"))
    texts = list(dict.fromkeys(t.strip() for t in texts))
    todo = reader.missing(texts, reader.questions)
    calls = -(-len(todo) // QUESTIONS_PER_CALL)
    print(f"{len(texts)} clauses, {len(todo)} unanswered questions -> {calls} call(s) / credit(s)")
    if args.dry_run:
        return 0
    reader.ask(texts, reader.questions)
    reader.verify(reader.read(texts), {t: proposed_kinds(t) for t in texts})  # same checks the app makes
    left = reader.missing(texts, reader.questions)
    print(f"answered {len(todo) - len(left)}/{len(todo)}; credits left {reader.credits_remaining}; "
          f"charged {reader.credits_charged}")
    return 0 if not left else 1


if __name__ == "__main__":
    raise SystemExit(main())
