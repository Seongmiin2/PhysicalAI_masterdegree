from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import requests


def download_selected(catalog: Path, output: Path, max_bytes: int) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    downloaded = []
    with catalog.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        if row["selected"].lower() != "true":
            continue
        size = int(row["size_bytes"])
        if size > max_bytes:
            raise ValueError(f"Selected file exceeds limit: {row['file_name']} ({size} bytes)")
        destination = output / row["file_name"]
        response = requests.get(row["download_url"], timeout=60)
        response.raise_for_status()
        content = response.content
        if len(content) != size:
            raise ValueError(f"Size mismatch for {destination}: expected {size}, got {len(content)}")
        digest = hashlib.md5(content, usedforsecurity=False).hexdigest()
        if row["md5"] and digest != row["md5"]:
            raise ValueError(f"MD5 mismatch for {destination}")
        destination.write_bytes(content)
        downloaded.append(destination)
    return downloaded


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("configs/tep_file_catalog.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/tep/docs"))
    parser.add_argument("--max-bytes", type=int, default=10_000_000)
    args = parser.parse_args()
    print([str(path) for path in download_selected(args.catalog, args.output, args.max_bytes)])


if __name__ == "__main__":
    main()
