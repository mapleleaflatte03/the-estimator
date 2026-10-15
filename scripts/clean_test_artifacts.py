"""Remove records the old test suite wrote into the real workspace store.

Before tests were isolated (tests/conftest.py), test_api.py created projects
titled "Corporate Project Management Portal" with 175h actuals and the reason
"Frontend scope simplified, testing completed faster" in data/parallax_store.json.
Those fake completions would otherwise enter the reference class.

Dry run by default. Use --apply to write; a timestamped backup is kept.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

STORE = Path(__file__).resolve().parent.parent / "data" / "parallax_store.json"
TEST_TITLES = {"Corporate Project Management Portal", "Test"}
TEST_REASON = "Frontend scope simplified, testing completed faster"


def main() -> int:
    store = Path(sys.argv[sys.argv.index("--store") + 1]) if "--store" in sys.argv else STORE
    data = json.loads(store.read_text(encoding="utf-8"))
    doomed = []
    for p in data.get("projects", []):
        acts = data.get("actuals", {}).get(p["project_id"], [])
        fake_actual = any(TEST_REASON in a.get("deviation_reasons", []) for a in acts)
        if p["title"] in TEST_TITLES and (fake_actual or not acts):
            doomed.append(p["project_id"])
            print(f"remove {p['project_id']}  {p['title']!r}  actuals={[a['actual_hours'] for a in acts]}")
    if not doomed:
        print("nothing to clean")
        return 0
    if "--apply" not in sys.argv:
        print(f"\n{len(doomed)} project(s) would be removed. Re-run with --apply to write (backup is kept).")
        return 0
    backup = store.with_name(f"{store.stem}.backup-{datetime.now():%Y%m%d-%H%M%S}.json")
    shutil.copy2(store, backup)
    data["projects"] = [p for p in data["projects"] if p["project_id"] not in doomed]
    for key in ("versions", "actuals"):
        data[key] = {k: v for k, v in data.get(key, {}).items() if k not in doomed}
    cal = data.get("calibration")
    if cal:
        cal["observations"] = [o for o in cal.get("observations", []) if o["project_id"] not in doomed]
    store.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"removed {len(doomed)} project(s); backup at {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
