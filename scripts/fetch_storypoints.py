"""Download the Choetkiertikul et al. story-point dataset (the Deep-SE benchmark) into datasets/external/deepse/.

Source: M. Choetkiertikul, H. K. Dam, T. Tran, T. Pham, A. Ghose, T. Menzies, "A Deep Learning Model for
Estimating Story Points", IEEE Transactions on Software Engineering 45(7):637-656, 2019,
doi:10.1109/TSE.2018.2792473. Data: https://github.com/morakotch/datasets (folder storypoint/IEEE TSE2018),
pinned to commit 133a5f59e7699a5612cbbc036b8d111844ad12cd. 23,313 issues from 16 open-source projects
(title, description, story points) plus the authors' chronological train/validation/test split files.
The repository declares no licence, so the files are downloaded on demand and not redistributed here.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

COMMIT = "133a5f59e7699a5612cbbc036b8d111844ad12cd"
BASE = f"https://raw.githubusercontent.com/morakotch/datasets/{COMMIT}/storypoint/IEEE%20TSE2018/"
PROJECTS = ("appceleratorstudio", "aptanastudio", "bamboo", "clover", "datamanagement", "duracloud", "jirasoftware",
            "mesos", "moodle", "mule", "mulestudio", "springxd", "talenddataquality", "talendesb", "titanium", "usergrid")
OUT = Path(__file__).resolve().parent.parent / "datasets" / "external" / "deepse"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"source": "https://github.com/morakotch/datasets", "commit": COMMIT,
                "paper": "doi:10.1109/TSE.2018.2792473", "files": {}}
    for p in PROJECTS:
        for rel, name in ((f"dataset/{p}.csv", f"{p}.csv"), (f"Deep-SE/data/{p}_3sets.txt", f"{p}_3sets.txt")):
            target = OUT / name
            if not target.exists():
                urllib.request.urlretrieve(BASE + urllib.parse.quote(rel), target)
            manifest["files"][name] = hashlib.sha256(target.read_bytes()).hexdigest()
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"{len(manifest['files'])} files in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
