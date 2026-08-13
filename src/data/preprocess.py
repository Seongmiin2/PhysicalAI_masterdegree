from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_config

STATE = ["reactor_pressure", "reactor_temperature", "reactor_level", "separator_level"]
ACTION = ["feed_valve", "purge_valve", "cooling_water", "agitator_speed"]


def split_for_episode(index: int, count: int, train: float, validation: float) -> str:
    fraction = index / max(count, 1)
    if fraction < train:
        return "train"
    if fraction < train + validation:
        return "validation"
    return "test"


def preprocess(raw_path: Path, output: Path, config: dict) -> dict:
    frame = pd.read_parquet(raw_path).sort_values(["episode_id", "step"])
    episode_ids = sorted(frame["episode_id"].unique())
    split_map = {episode_id: split_for_episode(i, len(episode_ids), config["train_fraction"], config["validation_fraction"]) for i, episode_id in enumerate(episode_ids)}
    frame["split"] = frame["episode_id"].map(split_map)
    normal_train = frame[(frame["split"] == "train") & (frame["fault_active"] == 0)]
    columns = STATE + ACTION
    means = normal_train[columns].mean()
    stds = normal_train[columns].std().replace(0, 1).fillna(1)
    frame[columns] = (frame[columns] - means) / stds
    window = int(config["window"])
    xs, ys, episodes, splits = [], [], [], []
    for episode_id, group in frame.groupby("episode_id", sort=False):
        values = group[columns].to_numpy(dtype=np.float32)
        label = int(group["recovery_success"].iloc[0])
        for end in range(window, len(values)):
            xs.append(values[end - window:end])
            ys.append(label)
            episodes.append(episode_id)
            splits.append(split_map[episode_id])
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / "windows.npz", x=np.asarray(xs, dtype=np.float32), y=np.asarray(ys, dtype=np.int64), episode=np.asarray(episodes), split=np.asarray(splits))
    frame.to_parquet(output / "telemetry.parquet", index=False)
    stats = {"features": columns, "mean": means.to_dict(), "std": stds.to_dict(), "window": window}
    (output / "preprocess.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return {"rows": len(frame), "windows": len(xs), "episodes": len(episode_ids)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    raw = Path(config["paths"]["raw"]) / "synthetic_episodes.parquet"
    print(preprocess(raw, Path(config["paths"]["processed"]), config))


if __name__ == "__main__":
    main()
