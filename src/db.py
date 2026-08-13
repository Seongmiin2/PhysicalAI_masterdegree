from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS Experiment (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, dataset TEXT NOT NULL,
 config_json TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed')),
 started_at TEXT, finished_at TEXT, error TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS RecoveryEpisode (
 id INTEGER PRIMARY KEY, external_id TEXT NOT NULL UNIQUE,
 experiment_id INTEGER REFERENCES Experiment(id), telemetry_path TEXT NOT NULL,
 split TEXT NOT NULL CHECK(split IN ('train','validation','test')),
 operating_mode TEXT NOT NULL, fault_type TEXT NOT NULL, current_state TEXT NOT NULL,
 candidate_action TEXT NOT NULL, action_sequence TEXT NOT NULL,
 recovery_success INTEGER NOT NULL CHECK(recovery_success IN (0,1)), recovery_time REAL,
 constraint_violation INTEGER NOT NULL CHECK(constraint_violation IN (0,1)),
 unsafe_state INTEGER NOT NULL CHECK(unsafe_state IN (0,1)), applicability_label TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS FaultEvent (
 id INTEGER PRIMARY KEY, episode_id INTEGER NOT NULL REFERENCES RecoveryEpisode(id) ON DELETE CASCADE,
 fault_type TEXT NOT NULL, onset_step INTEGER NOT NULL, severity REAL NOT NULL, details_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS RecoveryAction (
 id INTEGER PRIMARY KEY, episode_id INTEGER NOT NULL REFERENCES RecoveryEpisode(id) ON DELETE CASCADE,
 step INTEGER NOT NULL, action_type TEXT NOT NULL, parameters_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS RecoveryOutcome (
 id INTEGER PRIMARY KEY, episode_id INTEGER NOT NULL UNIQUE REFERENCES RecoveryEpisode(id) ON DELETE CASCADE,
 success INTEGER NOT NULL, unsafe INTEGER NOT NULL, recovery_time REAL,
 constraint_violation INTEGER NOT NULL, final_state_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ModelRun (
 id INTEGER PRIMARY KEY, experiment_id INTEGER NOT NULL REFERENCES Experiment(id), model_name TEXT NOT NULL,
 checkpoint_path TEXT, status TEXT NOT NULL, parameters_json TEXT NOT NULL,
 started_at TEXT DEFAULT CURRENT_TIMESTAMP, finished_at TEXT
);
CREATE TABLE IF NOT EXISTS Metric (
 id INTEGER PRIMARY KEY, model_run_id INTEGER NOT NULL REFERENCES ModelRun(id) ON DELETE CASCADE,
 split TEXT NOT NULL, name TEXT NOT NULL, value REAL NOT NULL, metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_episode_split ON RecoveryEpisode(split);
CREATE INDEX IF NOT EXISTS idx_episode_fault ON RecoveryEpisode(fault_type);
CREATE INDEX IF NOT EXISTS idx_episode_outcome ON RecoveryEpisode(recovery_success, unsafe_state);
"""


@contextmanager
def connect(path: str | Path) -> Iterator[sqlite3.Connection]:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=60)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize(path: str | Path) -> None:
    with connect(path) as connection:
        connection.executescript(SCHEMA)


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
