from __future__ import annotations

import argparse
import json
import logging
import random
import traceback
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from src.config import load_config
from src.data.preprocess import preprocess, split_for_episode
from src.db import connect, initialize, json_text
from src.models.state_encoder import StateEncoder
from src.simulator.generate_episode import generate

LOGGER = logging.getLogger(__name__)


def now() -> str:
    return datetime.now(UTC).isoformat()


def configure_log(path: str) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()])


def persist_episodes(db_path: str, experiment_id: int, episodes: pd.DataFrame, telemetry_path: Path, config: dict) -> None:
    with connect(db_path) as connection:
        for index, episode in episodes.iterrows():
            split = split_for_episode(index, len(episodes), config["train_fraction"], config["validation_fraction"])
            cursor = connection.execute("""INSERT OR IGNORE INTO RecoveryEpisode
                (external_id,experiment_id,telemetry_path,split,operating_mode,fault_type,current_state,candidate_action,action_sequence,recovery_success,recovery_time,constraint_violation,unsafe_state,applicability_label)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (episode.external_id, experiment_id, str(telemetry_path), split, episode.operating_mode, episode.fault_type, json_text(episode.current_state), episode.candidate_action, json_text(episode.action_sequence), int(episode.recovery_success), episode.recovery_time, int(episode.constraint_violation), int(episode.unsafe_state), episode.applicability_label))
            row = connection.execute("SELECT id FROM RecoveryEpisode WHERE external_id=?", (episode.external_id,)).fetchone()
            episode_id = int(row["id"])
            if cursor.rowcount:
                connection.execute("INSERT INTO FaultEvent(episode_id,fault_type,onset_step,severity) VALUES(?,?,?,?)", (episode_id, episode.fault_type, int(episode.fault_onset), float(episode.severity)))
                connection.execute("INSERT INTO RecoveryAction(episode_id,step,action_type,parameters_json) VALUES(?,?,?,?)", (episode_id, int(episode.action_step), episode.candidate_action, "{}"))
                connection.execute("INSERT INTO RecoveryOutcome(episode_id,success,unsafe,recovery_time,constraint_violation,final_state_json) VALUES(?,?,?,?,?,?)", (episode_id, int(episode.recovery_success), int(episode.unsafe_state), episode.recovery_time, int(episode.constraint_violation), json_text(episode.current_state)))


def evaluate(model: StateEncoder, x: torch.Tensor, y: torch.Tensor) -> tuple[float, float]:
    if len(x) == 0:
        return float("nan"), float("nan")
    model.eval()
    with torch.no_grad():
        _, logits = model(x)
        loss = nn.functional.binary_cross_entropy_with_logits(logits, y.float()).item()
        accuracy = ((logits.sigmoid() >= 0.5) == y.bool()).float().mean().item()
    return loss, accuracy


def train(config: dict, experiment_id: int) -> dict[str, float]:
    data = np.load(Path(config["paths"]["processed"]) / "windows.npz")
    x = torch.from_numpy(data["x"])
    y = torch.from_numpy(data["y"])
    splits = data["split"].astype(str)
    train_mask, val_mask, test_mask = splits == "train", splits == "validation", splits == "test"
    model = StateEncoder(x.shape[-1], int(config["hidden_dim"]), int(config["embedding_dim"]))
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"]))
    loader = DataLoader(TensorDataset(x[train_mask], y[train_mask]), batch_size=int(config["batch_size"]), shuffle=True)
    with connect(config["paths"]["database"]) as connection:
        model_run_id = connection.execute("INSERT INTO ModelRun(experiment_id,model_name,status,parameters_json) VALUES(?,?,?,?)", (experiment_id, "gru_state_encoder", "running", json_text({"hidden_dim": config["hidden_dim"], "embedding_dim": config["embedding_dim"]}))).lastrowid
    for epoch in range(int(config["epochs"])):
        model.train()
        total = 0.0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            _, logits = model(batch_x)
            loss = nn.functional.binary_cross_entropy_with_logits(logits, batch_y.float())
            loss.backward()
            optimizer.step()
            total += loss.item() * len(batch_x)
        val_loss, val_accuracy = evaluate(model, x[val_mask], y[val_mask])
        LOGGER.info("epoch=%d train_loss=%.6f val_loss=%.6f val_accuracy=%.4f", epoch + 1, total / len(loader.dataset), val_loss, val_accuracy)
    checkpoint = Path(config["paths"]["checkpoint"])
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state": model.state_dict(), "config": config}, checkpoint)
    test_loss, test_accuracy = evaluate(model, x[test_mask], y[test_mask])
    metrics = {"test_loss": test_loss, "test_accuracy": test_accuracy}
    with connect(config["paths"]["database"]) as connection:
        connection.execute("UPDATE ModelRun SET status='completed',checkpoint_path=?,finished_at=? WHERE id=?", (str(checkpoint), now(), model_run_id))
        for name, value in metrics.items():
            connection.execute("INSERT INTO Metric(model_run_id,split,name,value) VALUES(?,?,?,?)", (model_run_id, "test", name, value))
    return metrics


def run(config_path: str) -> dict[str, float]:
    config = load_config(config_path)
    configure_log(config["paths"]["log"])
    seed = int(config["seed"])
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    initialize(config["paths"]["database"])
    with connect(config["paths"]["database"]) as connection:
        experiment_id = connection.execute("INSERT INTO Experiment(name,dataset,config_json,status,started_at) VALUES(?,?,?,?,?)", ("recovery_episode_baseline", config["dataset"], json_text(config), "running", now())).lastrowid
    try:
        LOGGER.info("Generating %d synthetic TEP recovery episodes", config["episodes"])
        telemetry, episodes = generate(config)
        raw_dir = Path(config["paths"]["raw"]); raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / "synthetic_episodes.parquet"
        telemetry.to_parquet(raw_path, index=False)
        episodes.to_json(raw_dir / "episodes.jsonl", orient="records", lines=True, force_ascii=False)
        persist_episodes(config["paths"]["database"], experiment_id, episodes, raw_path, config)
        LOGGER.info("Preprocessing telemetry")
        summary = preprocess(raw_path, Path(config["paths"]["processed"]), config)
        LOGGER.info("Preprocess summary: %s", summary)
        metrics = train(config, experiment_id)
        with connect(config["paths"]["database"]) as connection:
            connection.execute("UPDATE Experiment SET status='completed',finished_at=? WHERE id=?", (now(), experiment_id))
        LOGGER.info("Completed: %s", metrics)
        return metrics
    except Exception as error:
        LOGGER.error("Experiment failed\n%s", traceback.format_exc())
        with connect(config["paths"]["database"]) as connection:
            connection.execute("UPDATE Experiment SET status='failed',finished_at=?,error=? WHERE id=?", (now(), str(error), experiment_id))
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline.yaml")
    args = parser.parse_args()
    print(json.dumps(run(args.config), indent=2))


if __name__ == "__main__":
    main()
