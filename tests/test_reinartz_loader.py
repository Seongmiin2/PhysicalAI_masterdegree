import pytest

from src.data.reinartz import validate_headers


def test_label_alignment_schema() -> None:
    validate_headers(["run_id", "sample", "xmeas_1"], ["run_id", "sample", "labels"], ["run_id", "sample", "train_mask"], ["run_id", "sample", "test_mask"])


def test_leakage_guard() -> None:
    with pytest.raises(ValueError, match="Leakage"):
        validate_headers(["run_id", "sample", "labels"], ["run_id", "sample", "labels"], ["run_id", "sample", "train_mask"], ["run_id", "sample", "test_mask"])
