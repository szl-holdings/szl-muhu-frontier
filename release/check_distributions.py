"""Fail-closed wheel/sdist content audit; do not ship private eval or public training rows."""
from __future__ import annotations

from pathlib import Path
import json
import tarfile
import zipfile

HERE = Path(__file__).resolve().parents[1]
DIST = HERE / "dist"
SENSITIVE = (
    "/dataset/", "/research/", "/tests/", "/.git/", "/.github/",
    "/release/", "/cloudflare/", "/private/",
)
BANNED_ENDINGS = (".jsonl", ".pkl", ".pickle", ".safetensors", ".ckpt", ".pem", ".key")
NAME = "szl_muhu_evidence-0.1.0"
EXPECTED_WHEEL = NAME + "-py3-none-any.whl"
EXPECTED_SDIST = NAME + ".tar.gz"


def verify() -> dict:
    wheel = DIST / EXPECTED_WHEEL
    source = DIST / EXPECTED_SDIST
    if not wheel.is_file() or not source.is_file():
        raise ValueError("MISSING_EXACT_RELEASE_ARTIFACTS")
    with zipfile.ZipFile(wheel) as z:
        wheel_entries = z.namelist()
        if z.testzip() is not None:
            raise ValueError("WHEEL_ZIP_DAMAGED")
    with tarfile.open(source, "r:gz") as t:
        sdist_entries = t.getnames()
    for path in [*wheel_entries, *sdist_entries]:
        p = "/" + path.replace("\\", "/").lower()
        if ".." in p.split("/") or p.startswith("//"):
            raise ValueError("ARCHIVE_PATH_TRAVERSAL")
        if any(x in p for x in SENSITIVE):
            raise ValueError("PRIVATE_OR_NONPACKAGE_ARTIFACT_INCLUDED:" + path)
        if p.endswith(BANNED_ENDINGS):
            raise ValueError("BANNED_BINARY_OR_TRAINING_DATA:" + path)
    required = (
        "muhu/cli.py", "muhu/core.py", "muhu/witness.py",
        "muhu/x402.py", "muhu/release_proof.py",
    )
    if not all(any(p.endswith(v) for p in wheel_entries) for v in required):
        raise ValueError("PUBLIC_API_WHEEL_MODULES_MISSING")
    if any(p.endswith(".json") for p in wheel_entries):
        raise ValueError("WHEEL_SHOULD_NOT_BUNDLE_PUBLICATION_SNAPSHOTS")
    return {
        "state": "SOURCE_AND_WHEEL_INSPECTED_NO_DATASETS",
        "wheel_entries": len(wheel_entries),
        "sdist_entries": len(sdist_entries),
        "published": False,
        "private_eval_included": False,
        "training_data_included": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
