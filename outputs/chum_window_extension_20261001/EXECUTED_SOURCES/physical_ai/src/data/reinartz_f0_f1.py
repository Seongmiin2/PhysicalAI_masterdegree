from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

N_RUNS = 2800
N_SAMPLES = 2000
N_XMEAS = 41
N_XMV = 11
N_FEATURES = N_XMEAS + N_XMV
FAULT_ONSET = 600


def build_cache(source: Path, cache: Path, chunksize: int = 50_000) -> dict:
    cache.mkdir(parents=True, exist_ok=True)
    feature_path = cache / "features.npy"
    metadata_path = cache / "metadata.npz"
    manifest_path = cache / "cache_manifest.json"
    if feature_path.exists() and metadata_path.exists() and manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    features = np.lib.format.open_memmap(
        feature_path, mode="w+", dtype=np.float32, shape=(N_RUNS, N_SAMPLES, N_FEATURES)
    )
    run_ids = np.empty(N_RUNS, dtype=np.int64)
    row = 0
    for chunk in pd.read_csv(source / "dataset.csv", chunksize=chunksize):
        length = len(chunk)
        positions = np.arange(row, row + length)
        expected_sample = positions % N_SAMPLES + 1
        if not np.array_equal(chunk["sample"].to_numpy(), expected_sample):
            raise ValueError("Dataset is not ordered by contiguous run/sample")
        run_position = positions // N_SAMPLES
        run_starts = expected_sample == 1
        run_ids[run_position[run_starts]] = chunk.loc[run_starts, "run_id"].to_numpy(dtype=np.int64)
        features.reshape(-1, N_FEATURES)[row : row + length] = chunk.iloc[:, 2:].to_numpy(
            dtype=np.float32
        )
        row += length
    features.flush()
    if row != N_RUNS * N_SAMPLES or np.count_nonzero(run_ids) != N_RUNS:
        raise ValueError(f"Cache shape mismatch: rows={row}, runs={np.count_nonzero(run_ids)}")
    labels = pd.read_csv(source / "labels.csv")
    train = pd.read_csv(source / "train_mask.csv")
    test = pd.read_csv(source / "test_mask.csv")
    if not (labels[["run_id", "sample"]].equals(train[["run_id", "sample"]]) and labels[["run_id", "sample"]].equals(test[["run_id", "sample"]])):
        raise ValueError("Label/mask index alignment failed")
    label_array = labels["labels"].to_numpy(dtype=np.int16).reshape(N_RUNS, N_SAMPLES)
    train_array = train["train_mask"].to_numpy(dtype=bool).reshape(N_RUNS, N_SAMPLES)
    test_array = test["test_mask"].to_numpy(dtype=bool).reshape(N_RUNS, N_SAMPLES)
    if np.any(train_array & test_array):
        raise ValueError("Train/test row overlap")
    if np.any(train_array != train_array[:, :1]) or np.any(test_array != test_array[:, :1]):
        raise ValueError("Masks vary within a run")
    np.savez_compressed(
        metadata_path,
        run_ids=run_ids,
        labels=label_array,
        train_run=train_array[:, 0],
        test_run=test_array[:, 0],
    )
    manifest = {
        "rows": row,
        "runs": N_RUNS,
        "samples_per_run": N_SAMPLES,
        "features": N_FEATURES,
        "dtype": "float32",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def create_split(metadata_path: Path, seed: int, validation_per_fault: int) -> pd.DataFrame:
    metadata = np.load(metadata_path)
    labels = metadata["labels"]
    run_ids = metadata["run_ids"]
    train_mask = metadata["train_run"]
    test_mask = metadata["test_run"]
    rng = np.random.default_rng(seed)
    records = []
    for fault_id in range(1, 29):
        fault_runs = np.flatnonzero(labels[:, -1] == fault_id)
        original_train = fault_runs[train_mask[fault_runs]]
        original_test = fault_runs[test_mask[fault_runs]]
        if len(original_train) != 80 or len(original_test) != 20:
            raise ValueError(f"Unexpected split counts for fault {fault_id}")
        validation = set(rng.choice(original_train, validation_per_fault, replace=False).tolist())
        for run_index in fault_runs:
            split = "test" if run_index in original_test else "validation" if run_index in validation else "train"
            records.append({"run_index": run_index, "run_id": run_ids[run_index], "fault_id": fault_id, "split": split, "n_samples": N_SAMPLES, "fault_onset": FAULT_ONSET})
    result = pd.DataFrame(records).sort_values("run_index").reset_index(drop=True)
    if result.groupby("run_id")["split"].nunique().max() != 1:
        raise ValueError("Run leakage across split")
    return result


def fit_scaler(features: np.ndarray, train_runs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    normal = np.asarray(features[train_runs, : FAULT_ONSET - 1, :], dtype=np.float64)
    mean = normal.mean(axis=(0, 1))
    std = normal.std(axis=(0, 1))
    std[std == 0] = 1.0
    return mean.astype(np.float32), std.astype(np.float32)
