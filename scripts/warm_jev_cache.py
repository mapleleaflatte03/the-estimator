"""Pre-compute Jev readings for the sample briefs into datasets/jev_cache/ (shipped with the app).

Sample briefs then show AI readings on the live site without spending credits,
and every visitor gets the same, consistent result. Already-cached clauses are free.
Usage: python scripts/warm_jev_cache.py [--dry-run]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from parallax.extractor import clause_texts  # noqa: E402
from parallax.jev import CLAUSES_PER_CALL, SHIPPED_CACHE, JevReader  # noqa: E402


def main() -> int:
    reader = JevReader(cache_path=SHIPPED_CACHE)
    texts = []
    for path in sorted((ROOT / "datasets" / "golden_briefs").glob("*.json")):
        texts += clause_texts(json.loads(path.read_text(encoding="utf-8"))["brief_text"])
    todo = [t for t in dict.fromkeys(texts) if reader.cached(t) is None]
    calls = -(-len(todo) // CLAUSES_PER_CALL)
    print(f"{len(texts)} clauses in sample briefs, {len(todo)} not cached -> {calls} call(s)")
    if "--dry-run" in sys.argv or not todo:
        return 0
    got = reader.read(todo)
    print(f"read {len(got)}/{len(todo)}; status: {reader.status()}")
    return 0 if len(got) == len(todo) else 1


if __name__ == "__main__":
    raise SystemExit(main())
