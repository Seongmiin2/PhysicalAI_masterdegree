from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import requests

ARTICLE_ID = 13385936
API_URL = f"https://api.figshare.com/v2/articles/{ARTICLE_ID}"
DOCUMENT_PATTERN = re.compile(
    r"(readme|metadata|description|variable|column|codebook|documentation)", re.IGNORECASE
)


def fetch_catalog(output: Path, raw_metadata: Path) -> list[dict]:
    response = requests.get(API_URL, timeout=60)
    response.raise_for_status()
    article = response.json()
    raw_metadata.parent.mkdir(parents=True, exist_ok=True)
    raw_metadata.write_text(json.dumps(article, indent=2, ensure_ascii=False), encoding="utf-8")
    rows = []
    for item in article.get("files", []):
        name = item["name"]
        selected = bool(DOCUMENT_PATTERN.search(name))
        rows.append(
            {
                "file_id": item["id"],
                "file_name": name,
                "size_bytes": item["size"],
                "download_url": item["download_url"],
                "md5": item.get("supplied_md5") or item.get("computed_md5") or "",
                "selected": str(selected).lower(),
                "notes": "documentation candidate" if selected else "not downloaded during catalog step",
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["file_id", "file_name", "size_bytes", "download_url", "md5", "selected", "notes"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("configs/tep_file_catalog.csv"))
    parser.add_argument("--raw-metadata", type=Path, default=Path("data/raw/tep/article_13385936.json"))
    args = parser.parse_args()
    rows = fetch_catalog(args.output, args.raw_metadata)
    selected = sum(row["selected"] == "true" for row in rows)
    print({"files": len(rows), "selected_document_candidates": selected, "catalog": str(args.output)})


if __name__ == "__main__":
    main()
