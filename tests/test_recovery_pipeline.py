from __future__ import annotations

import sqlite3

from src.data.preprocess import split_for_episode
from src.db import initialize
from src.simulator.generate_episode import CORRECT, generate


def small_config() -> dict:
    return {
        "seed": 7,
        "episodes": 8,
        "steps_per_episode": 24,
        "sample_seconds": 180,
        "unsafe_pressure": 3300.0,
        "unsafe_temperature": 175.0,
    }


def test_episode_generator_is_deterministic() -> None:
    telemetry_a, episodes_a = generate(small_config())
    telemetry_b, episodes_b = generate(small_config())
    assert telemetry_a.equals(telemetry_b)
    assert episodes_a.equals(episodes_b)
    assert len(telemetry_a) == 8 * 24
    assert set(episodes_a["applicability_label"]) <= {"applicable", "not_applicable"}
    for episode in episodes_a.itertuples():
        expected = CORRECT[episode.fault_type]
        assert (episode.candidate_action == expected) == (episode.applicability_label == "applicable")


def test_split_is_episode_level() -> None:
    assert split_for_episode(0, 100, 0.7, 0.15) == "train"
    assert split_for_episode(70, 100, 0.7, 0.15) == "validation"
    assert split_for_episode(85, 100, 0.7, 0.15) == "test"


def test_sqlite_schema(tmp_path) -> None:
    database = tmp_path / "experiment.db"
    initialize(database)
    with sqlite3.connect(database) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"Experiment", "RecoveryEpisode", "FaultEvent", "RecoveryAction", "RecoveryOutcome", "ModelRun", "Metric"} <= tables
