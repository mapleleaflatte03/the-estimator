"""Test isolation: never let tests write into the real workspace store."""
import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="parallax-test-"))
os.environ["PARALLAX_DATA_PATH"] = str(_TMP / "store.json")
# Never call a paid AI provider from tests; reader logic is tested with fake readings.
os.environ["JEV_DISABLED"] = "1"
for _k in ("JEVSTATION_API_KEY", "TYPESAFE_API_KEY", "AI_GATEWAY_API_KEY"):
    os.environ.pop(_k, None)
