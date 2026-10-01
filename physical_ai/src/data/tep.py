from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

XMEAS = [f"XMEAS_{index:02d}" for index in range(1, 42)]
XMV = [f"XMV_{index:02d}" for index in range(1, 13)]
CANONICAL = ["run_id", "sample_idx", "time", "operating_mode", "fault_id", "fault_onset", *XMEAS, *XMV]


@dataclass(frozen=True)
class RunIdentity:
    run_id: str
    operating_mode: int
    fault_id: int


def decode_labels(values: np.ndarray) -> list[str]:
    return [value.decode(errors="replace").strip() if isinstance(value, bytes) else str(value).strip() for value in values.reshape(-1)]


def identify_run(path: str) -> RunIdentity:
    mode = re.search(r"(?:^|/)Mode(\d+)(?:/|$)", path)
    fault = re.search(r"(?:^|/)IDV(\d+)(?:/|$)", path)
    run = re.search(r"(?:^|/)(Run\d+)(?:/|$)", path)
    if not (mode and fault and run):
        raise ValueError(f"Cannot identify Mode/IDV/Run from HDF5 path: {path}")
    return RunIdentity(run_id=path, operating_mode=int(mode.group(1)), fault_id=int(fault.group(1)))


def load_run(file_path: str | Path, run_path: str) -> pd.DataFrame:
    with h5py.File(file_path, "r") as handle:
        if run_path not in handle:
            raise KeyError(f"Run path not found: {run_path}")
        group = handle[run_path]
        if "processdata" not in group:
            raise KeyError(f"processdata missing from {run_path}")
        labels = decode_labels(handle["Processdata_Labels"][...])
        values = np.asarray(group["processdata"][...])
        if values.ndim != 2:
            raise ValueError(f"Expected 2-D processdata, found shape {values.shape}")
        if values.shape[1] != len(labels) and values.shape[0] == len(labels):
            values = values.T
        if values.shape[1] != len(labels):
            raise ValueError(f"Label/data mismatch: {len(labels)} labels vs shape {values.shape}")
        source = pd.DataFrame(values, columns=labels)
        identity = identify_run(run_path)
        xmeas_source = [
            name for name in labels if re.search(r"XMEAS\D*\d+", name, re.IGNORECASE)
        ]
        xmv_source = [
            name for name in labels if re.search(r"XMV\D*\d+", name, re.IGNORECASE)
        ]
        if len(xmeas_source) != 41 or len(xmv_source) != 12:
            raise ValueError(f"Expected 41 XMEAS and 12 XMV labels, found {len(xmeas_source)} and {len(xmv_source)}")
        frame = pd.DataFrame({"run_id": identity.run_id, "sample_idx": np.arange(len(source)), "time": source[labels[0]], "operating_mode": identity.operating_mode, "fault_id": identity.fault_id, "fault_onset": np.nan})
        frame[XMEAS] = source[xmeas_source].to_numpy()
        frame[XMV] = source[xmv_source].to_numpy()
        return frame[CANONICAL]
