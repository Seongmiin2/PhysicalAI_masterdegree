from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cmapss import summarize


def validate_cmapss(root: Path) -> dict[str, dict[str, int]]:
    files = sorted(root.rglob("train_FD*.txt"))
    if not files:
        raise FileNotFoundError(f"No train_FD*.txt files found under {root}")
    return {file.stem: summarize(file) for file in files}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["cmapss"], required=True)
    parser.add_argument("--root", type=Path, default=Path("data/raw/cmapss"))
    args = parser.parse_args()
    report = validate_cmapss(args.root)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

