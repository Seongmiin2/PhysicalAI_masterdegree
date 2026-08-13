from __future__ import annotations

from pathlib import Path

import pandas as pd

NAMES = (
    ["unit_id", "cycle"]
    + [f"operational_setting_{i}" for i in range(1, 4)]
    + [f"sensor_{i}" for i in range(1, 22)]
)


def load_split(path: Path) -> pd.DataFrame:
    """Load one NASA C-MAPSS whitespace-delimited train/test file."""
    frame = pd.read_csv(path, sep=r"\s+", header=None, names=NAMES)
    if frame.shape[1] != len(NAMES):
        raise ValueError(f"Expected {len(NAMES)} columns, found {frame.shape[1]} in {path}")
    return frame


def summarize(path: Path) -> dict[str, int]:
    frame = load_split(path)
    return {
        "rows": len(frame),
        "runs": int(frame["unit_id"].nunique()),
        "variables": len(frame.columns),
        "nulls": int(frame.isna().sum().sum()),
    }

