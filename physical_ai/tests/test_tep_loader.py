from __future__ import annotations

import h5py
import numpy as np

from src.data.tep import CANONICAL, load_run


def test_load_run_to_canonical_schema(tmp_path) -> None:
    path = tmp_path / "mode1.h5"
    labels = ["Time", *[f"XMEAS({i})" for i in range(1, 42)], *[f"XMV({i})" for i in range(1, 13)]]
    with h5py.File(path, "w") as handle:
        handle.create_dataset("Processdata_Labels", data=np.asarray(labels, dtype="S16"))
        group = handle.create_group("Mode1/SingleFault/SimulationCompleted/IDV1/Case/Run1")
        group.create_dataset("processdata", data=np.arange(5 * len(labels)).reshape(5, len(labels)))
    frame = load_run(path, "/Mode1/SingleFault/SimulationCompleted/IDV1/Case/Run1")
    assert list(frame.columns) == CANONICAL
    assert frame.shape == (5, len(CANONICAL))
    assert frame["operating_mode"].unique().tolist() == [1]
    assert frame["fault_id"].unique().tolist() == [1]
