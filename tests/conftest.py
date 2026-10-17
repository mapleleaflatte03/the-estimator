"""Test isolation: never let tests write into the real workspace store or spend AI credits."""
import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="parallax-test-"))
os.environ["PARALLAX_DATA_PATH"] = str(_TMP / "store.json")
# Never call a paid AI provider from tests; reader logic is tested with fake readings.
os.environ["PARALLAX_NO_DOTENV"] = "1"
os.environ["JEV_DISABLED"] = "1"
# The shipped app refuses to estimate without the AI reader; API tests exercise the rest of the
# pipeline without it, and tests/test_ai_reader.py covers the required mode explicitly.
os.environ["JEV_REQUIRED"] = "0"
# The live service caps estimates per visitor. Tests share one client address.
os.environ["ESTIMATE_IP_LIMIT_PER_HOUR"] = "0"
for _k in list(os.environ):
    if _k.startswith(("JEVSTATION_API_KEY", "TYPESAFE_API_KEY", "AI_GATEWAY_API_KEY")):
        os.environ.pop(_k, None)
