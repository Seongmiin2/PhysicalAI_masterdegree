from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

from analyze_architecture_chum_sensitivity import build_architecture_cell_summary
from run_architecture_chum_sensitivity import completed_task_ids, expected_task_ids


def test_expected_sensitivity_grid_has_390_tasks() -> None:
    config = {
        "architectures": ["tcn", "transformer"],
        "seeds": [42, 43, 44, 45, 46],
        "primary_cells": [
            {"fault_id": 4, "channel": 10},
            {"fault_id": 19, "channel": 7},
            {"fault_id": 19, "channel": 8},
            {"fault_id": 25, "channel": 2},
        ],
        "residual_block_lengths": [5, 10, 20],
        "conditional_sample_draws": [1, 3, 10],
    }
    assert len(expected_task_ids(config)) == 390


def test_completed_task_requires_one_fault_and_all_runs() -> None:
    faults = pd.DataFrame([{"task_id": "task-a"}, {"task_id": "task-b"}])
    runs = pd.DataFrame(
        [
            {"task_id": "task-a", "run_index": index}
            for index in range(20)
        ]
        + [
            {"task_id": "task-b", "run_index": index}
            for index in range(19)
        ]
    )
    assert completed_task_ids(faults, runs, 20) == {"task-a"}


def test_architecture_cell_rule_is_strict() -> None:
    settings = pd.DataFrame(
        [
            {
                "architecture": "tcn",
                "fault_id": 4,
                "channel": 10,
                "block_length": block,
                "draws": draws,
                "direction_positive": True,
                "material_effect": not (block == 5 and draws == 1),
                "seed_stable": not (block == 5 and draws == 1),
                "fpr_guardrail_pass": True,
                "ci_positive": not (block == 5 and draws == 1),
                "setting_pass": not (block == 5 and draws == 1),
                "mean_delta_auroc": 0.10,
                "max_abs_pre_fpr_shift": 0.001,
            }
            for block in (5, 10, 20)
            for draws in (1, 3, 10)
        ]
    )
    rule = {
        "required_positive_settings": 9,
        "required_material_settings": 8,
        "required_seed_stable_settings": 8,
        "required_fpr_guardrail_settings": 9,
        "required_ci_positive_settings": 8,
    }
    result = build_architecture_cell_summary(settings, rule)
    assert bool(result.iloc[0].architecture_cell_robust)
