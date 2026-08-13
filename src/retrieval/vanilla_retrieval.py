from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.config import load_config
from src.db import connect


def retrieve(db_path: str | Path, state: dict[str, float], operating_mode: str, limit: int = 5) -> list[dict]:
    with connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM RecoveryEpisode WHERE operating_mode=? AND unsafe_state=0", (operating_mode,)).fetchall()
    query = np.array([state["pressure"], state["temperature"], state["level"]], dtype=float)
    scored = []
    for row in rows:
        candidate = json.loads(row["current_state"])
        vector = np.array([candidate["pressure"], candidate["temperature"], candidate["level"]], dtype=float)
        scale = np.array([500.0, 50.0, 30.0])
        scored.append((float(np.linalg.norm((query - vector) / scale)), dict(row)))
    return [{**row, "distance": distance} for distance, row in sorted(scored, key=lambda item: item[0])[:limit]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--mode", default="mode_1")
    args = parser.parse_args()
    config = load_config(args.config)
    result = retrieve(config["paths"]["database"], {"pressure": 2800, "temperature": 130, "level": 70}, args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
