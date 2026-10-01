import pytest

from providers.finetuned import record_text
from experiments.finetune_chum_ops import audit_splits, validate_run_outputs


def test_input_excludes_answer_and_label():
    record = {
        "label": "SECRET_LABEL",
        "messages": [
            {"role": "user", "content": "observed artifact"},
            {"role": "assistant", "content": "SECRET_ANSWER"},
        ],
        "provenance": {"group_id": "x"},
    }
    assert record_text(record) == "observed artifact"
    assert "SECRET" not in record_text({
        "status": "running", "label": "SECRET", "next_action": "SECRET",
    })


def test_group_leakage_is_rejected():
    row = {"provenance": {"group_id": "same_run"}}
    with pytest.raises(ValueError, match="leakage"):
        audit_splits({"train": [row], "test": [row]})


def test_disjoint_group_split_passes():
    audit_splits({
        "train": [{"provenance": {"group_id": "run1"}}],
        "test": [{"provenance": {"group_id": "run2"}}],
    })


def test_validate_run_outputs_preserves_prior_runs(tmp_path):
    output, report = tmp_path / "model", tmp_path / "report.json"
    validate_run_outputs(output, report, 3, 256, 2)
    with pytest.raises(ValueError, match="positive"):
        validate_run_outputs(output, report, 0, 256, 2)
    report.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Preserve"):
        validate_run_outputs(output, report, 3, 256, 2)
    report.unlink()
    output.mkdir()
    (output / "adapter_model.safetensors").write_bytes(b"existing")
    with pytest.raises(ValueError, match="Preserve"):
        validate_run_outputs(output, report, 3, 256, 2)