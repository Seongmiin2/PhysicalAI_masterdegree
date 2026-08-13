from __future__ import annotations

import argparse
import logging
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from src.config import load_config
from src.experiments.reinartz_f0_f1 import run_model
from src.models.reinartz_forecaster import GRUForecaster


LOGGER = logging.getLogger(__name__)
MODEL_SEED = 42
HIDDEN_DIM = 68


def parameter_count() -> int:
    return sum(parameter.numel() for parameter in GRUForecaster(41, HIDDEN_DIM, 1).parameters())


def load_fixed_inputs(config: dict) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    artifacts = Path(config["paths"]["artifacts"])
    split_path = artifacts / "reinartz_split_manifest.csv"
    scaler_path = artifacts / "reinartz_scaler_parameters.csv"
    if not split_path.exists() or not scaler_path.exists():
        raise FileNotFoundError("Existing Seed 42 split and scaler artifacts are required.")

    split = pd.read_csv(split_path)
    scaler = pd.read_csv(scaler_path)
    if len(scaler) != 52 or scaler["feature"].iloc[:41].tolist() != [f"xmeas_{i}" for i in range(1, 42)]:
        raise ValueError("Existing scaler feature order is invalid.")
    features = np.load(Path(config["paths"]["cache"]) / "features.npy", mmap_mode="r")
    return split, features, scaler["mean"].to_numpy(np.float32), scaler["std"].to_numpy(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/reinartz_f0_f1.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    if int(config["seed"]) != MODEL_SEED or int(config["epochs"]) != 30:
        raise ValueError("Capacity control requires split/model seed 42 and 30 epochs.")

    random.seed(MODEL_SEED)
    np.random.seed(MODEL_SEED)
    torch.manual_seed(MODEL_SEED)
    torch.use_deterministic_algorithms(True)

    log_dir = Path(config["paths"]["logs"])
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "capacity_control_seed_42.log", encoding="utf-8"),
        ],
    )
    LOGGER.info("=== F0-C capacity control started ===")
    LOGGER.info("XMEAS-only input_dim=41 hidden_dim=%d parameters=%d", HIDDEN_DIM, parameter_count())
    LOGGER.info("Using existing Seed 42 split and scaler artifacts; F0/F1 will not be trained.")

    split, features, mean, std = load_fixed_inputs(config)
    metrics, fault_rows = run_model(
        config, split, features, mean, std, "F0-C", 30, MODEL_SEED, hidden_dim=HIDDEN_DIM
    )
    artifacts = Path(config["paths"]["artifacts"])
    pd.DataFrame([metrics]).to_csv(artifacts / "reinartz_capacity_control_results.csv", index=False)
    pd.DataFrame(fault_rows).to_csv(artifacts / "reinartz_capacity_control_fault_results.csv", index=False)
    LOGGER.info("=== F0-C capacity control finished; result artifacts saved ===")


if __name__ == "__main__":
    main()
