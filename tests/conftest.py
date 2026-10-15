"""Test isolation: never let tests write into the real workspace store."""
import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="parallax-test-"))
os.environ["PARALLAX_DATA_PATH"] = str(_TMP / "store.json")
