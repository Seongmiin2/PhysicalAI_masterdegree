from __future__ import annotations

import pandas as pd

INDEX_COLUMNS = ["run_id", "sample"]
XMEAS_COLUMNS = [f"xmeas_{index}" for index in range(1, 42)]
EXPECTED_XMV_COLUMNS = [f"xmv_{index}" for index in range(1, 13)]


def semantic_mapping(columns: list[str]) -> pd.DataFrame:
    rows = []
    for column in columns:
        if column == "run_id":
            canonical, role, confidence = "run_id", "RUN_ID", "CONFIRMED"
        elif column == "sample":
            canonical, role, confidence = "sample_idx", "TIME", "LIKELY"
        elif column in XMEAS_COLUMNS:
            number = int(column.split("_")[1])
            canonical, role, confidence = f"XMEAS_{number:02d}", "STATE", "CONFIRMED"
        elif column in EXPECTED_XMV_COLUMNS:
            number = int(column.split("_")[1])
            canonical, role, confidence = f"XMV_{number:02d}", "ACTION_CANDIDATE", "CONFIRMED"
        else:
            canonical, role, confidence = "", "UNKNOWN", "UNKNOWN"
        rows.append(
            {
                "source_column": column,
                "canonical_variable": canonical,
                "semantic_role": role,
                "included": role in {"STATE", "ACTION_CANDIDATE"},
                "mapping_confidence": confidence,
                "notes": "sample order within run; physical time unit not encoded" if column == "sample" else "",
            }
        )
    missing = sorted(set(EXPECTED_XMV_COLUMNS) - set(columns))
    for column in missing:
        number = int(column.split("_")[1])
        rows.append(
            {
                "source_column": column,
                "canonical_variable": f"XMV_{number:02d}",
                "semantic_role": "ACTION_CANDIDATE",
                "included": False,
                "mapping_confidence": "CONFIRMED",
                "notes": "expected canonical variable absent from dataset.csv; removal reason UNKNOWN",
            }
        )
    return pd.DataFrame(rows)


def validate_headers(dataset: list[str], labels: list[str], train: list[str], test: list[str]) -> None:
    if dataset[:2] != INDEX_COLUMNS:
        raise ValueError("dataset.csv must begin with run_id,sample")
    if labels != [*INDEX_COLUMNS, "labels"]:
        raise ValueError("Unexpected labels.csv schema")
    if train != [*INDEX_COLUMNS, "train_mask"]:
        raise ValueError("Unexpected train_mask.csv schema")
    if test != [*INDEX_COLUMNS, "test_mask"]:
        raise ValueError("Unexpected test_mask.csv schema")
    forbidden = {"labels", "train_mask", "test_mask", "labeled_train_mask"}
    if forbidden.intersection(dataset):
        raise ValueError("Leakage column found in telemetry features")


def split_name(train_values: set[int], test_values: set[int]) -> str:
    train, test = 1 in train_values, 1 in test_values
    if train and test:
        return "LEAKED_BOTH"
    if train:
        return "train"
    if test:
        return "test"
    return "unassigned"
