import json
import pytest
from providers.ops_features import canonical_text, inference_text


def test_canonicalization_keeps_facts_and_excludes_targets_identifiers():
    raw = {"status": "RUNNING", "stage": "training", "epoch": 2,
           "label": "REVIEW_COMPLETED", "next_action": "REVIEW_COMPLETED",
           "task": "run-that-can-be-memorized", "path": "private", "updated_at": "yesterday"}
    text = canonical_text(raw)
    assert "RUNNING" in text and '"epoch":2' in text
    assert "REVIEW_COMPLETED" not in text
    assert "memorized" not in text and "private" not in text and "yesterday" not in text
    assert canonical_text(dict(reversed(list(raw.items())))) == text
    assert canonical_text(text) == text


def test_inference_does_not_include_teacher_or_classify_by_label():
    row = {"label": "REVIEW_COMPLETED", "messages": [
        {"role": "user", "content": '{"status":"RUNNING"}'},
        {"role": "assistant", "content": "REVIEW_COMPLETED"}]}
    assert "REVIEW_COMPLETED" not in inference_text(row, "normalized")
    assert inference_text(row, "raw") == '{"status":"RUNNING"}'
    with pytest.raises(ValueError):
        inference_text(row, "unregistered")


def test_inputs_are_not_assigned_invented_lifecycle_status():
    text = canonical_text({"artifact_type": "historical_training_epoch", "epoch": 3})
    assert "RUNNING" not in text
    assert "MONITOR" not in text
    assert canonical_text("inspect a log").startswith("Unstructured")
    with pytest.raises(ValueError):
        canonical_text({"label": "MONITOR_RUNNING"})
