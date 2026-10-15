"""Download the SiP dataset at the pinned commit and verify checksums.

The raw files are already committed under datasets/sip/; use this to restore
or re-verify them. Usage: python scripts/fetch_datasets.py [--verify-only]
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

COMMIT = "fed32c65e974bdcabd417c695508fed05f93c215"
BASE = f"https://raw.githubusercontent.com/Derek-Jones/SiP_dataset/{COMMIT}/"
FILES = {
    "Sip-task-info.csv": "28621aa8b0ce05c270085a78e96a4d37f1bb39c1a5d260059ff3c197de961a4a",
    "est-act-dates.csv": "4d5a5ea633969dd782ab3d6b2b0c6cf2fcc65d9bb1c22f332ac7d9abf5ead1e9",
    "LICENSE.md": None,
}
TARGET = Path(__file__).resolve().parent.parent / "datasets" / "sip"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    verify_only = "--verify-only" in sys.argv
    TARGET.mkdir(parents=True, exist_ok=True)
    ok = True
    for name, expected in FILES.items():
        path = TARGET / name
        if not verify_only:
            print(f"downloading {name}")
            urllib.request.urlretrieve(BASE + name, path)
        if expected:
            actual = sha256(path) if path.exists() else "missing"
            status = "OK" if actual == expected else f"MISMATCH ({actual})"
            ok &= actual == expected
            print(f"{name}: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
