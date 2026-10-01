"""Download the pinned public base model and verify every recorded file hash.

No training, inference, credentials, or project-data upload is performed.
Run from the project root using the environment with requirements-chum-finetune.txt:
    python experiments/download_chum_ops_base.py
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "outputs/chum_ops_training_20261001/BASE_MODEL_MANIFEST.json")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/harness/models/qwen2.5-0.5b-instruct")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    from huggingface_hub import snapshot_download
    snapshot_download(manifest["repository"], revision=manifest["revision"],
                      local_dir=str(args.output), allow_patterns=[f["path"] for f in manifest["files"]],
                      token=False)
    for item in manifest["files"]:
        path = args.output / item["path"]
        digest = hashlib.sha256()
        with path.open("rb") as reader:
            for block in iter(lambda: reader.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != item["sha256"]:
            raise RuntimeError(f"Base model hash mismatch: {item['path']}")
    print(json.dumps({"status": "VERIFIED", "revision": manifest["revision"],
                      "files": len(manifest["files"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
