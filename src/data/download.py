from __future__ import annotations

import argparse
import json
from pathlib import Path

TEP_LANDING = "https://data.dtu.dk/articles/dataset/13385936"


def main() -> None:
    parser = argparse.ArgumentParser(description="TEP acquisition guard")
    parser.add_argument("--dataset", choices=["tep"], default="tep")
    parser.add_argument("--output", type=Path, default=Path("data/raw/tep/source.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": "Extended Tennessee Eastman Reference Data",
        "landing_page": TEP_LANDING,
        "estimated_full_size_gb": 132.96,
        "policy": "manifest_only; never download-all in the baseline pipeline",
    }
    args.output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote metadata only: {args.output}")


if __name__ == "__main__":
    main()
