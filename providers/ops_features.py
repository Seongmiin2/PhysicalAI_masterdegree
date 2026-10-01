"""Canonical operational observations; no labels or inferred actions."""
from __future__ import annotations
import json

PREFIX = "Observed project facts:\n"
# Preserve lifecycle facts, not incidental task names, locations or timestamps.
FIELDS = ("status", "stage", "error", "event_kind", "artifact_type", "epoch",
          "epochs", "epochs_run", "best_epoch", "completed_tasks", "test_evaluated",
          "train_mse", "validation_mse", "best_validation_mse", "snapshot_semantics")


def canonical_text(value: str | dict) -> str:
    if isinstance(value, str):
        if value.startswith(PREFIX):
            return value
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            # Free prose has no reliably parsed fields. Preserve it as unstructured input.
            return "Unstructured project observation:\n" + value.strip()
    if not isinstance(value, dict):
        raise ValueError("An operational observation must be a JSON object or text")
    fields = {}
    for key in FIELDS:
        if key not in value:
            continue
        item = value[key]
        if isinstance(item, float):
            item = round(item, 6)
        fields[key] = item
    if not fields:
        raise ValueError("No supported observed operational facts")
    return PREFIX + json.dumps(fields, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def inference_text(record: dict, preprocessing: str = "raw") -> str:
    from .finetuned import record_text
    text = record_text(record)
    if preprocessing == "raw":
        return text
    if preprocessing != "normalized":
        raise ValueError("Unknown router preprocessing contract")
    return canonical_text(text)
