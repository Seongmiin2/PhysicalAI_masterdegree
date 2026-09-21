from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

from run_architecture_chum_g3 import MODEL_CLASSES, make_windows, metric_rows


ROOT = Path(__file__).resolve().parents[1]
ModelKey = tuple[str, int]


def resolve(path: str) -> Path:
    return (ROOT / path).resolve()


def task_id(
    architecture: str,
    seed: int,
    fault_id: int,
    channel: int | None,
    block_length: int | None,
    draws: int,
) -> str:
    if channel is None:
        return f"{architecture}|S{seed}|F{fault_id}|original"
    return (
        f"{architecture}|S{seed}|F{fault_id}|XMV{channel:02d}|"
        f"B{block_length:02d}|D{draws:02d}"
    )


def expected_task_ids(config: dict) -> set[str]:
    expected: set[str] = set()
    for architecture in config["architectures"]:
        for seed in config["seeds"]:
            for cell in config["primary_cells"]:
                fault_id = int(cell["fault_id"])
                channel = int(cell["channel"])
                expected.add(task_id(str(architecture), int(seed), fault_id, None, None, 1))
                for block_length in config["residual_block_lengths"]:
                    for draws in config["conditional_sample_draws"]:
                        expected.add(
                            task_id(
                                str(architecture),
                                int(seed),
                                fault_id,
                                channel,
                                int(block_length),
                                int(draws),
                            )
                        )
    return expected


def completed_task_ids(
    fault_rows: pd.DataFrame, run_rows: pd.DataFrame, expected_runs: int
) -> set[str]:
    if fault_rows.empty or run_rows.empty:
        return set()
    if "task_id" not in fault_rows or "task_id" not in run_rows:
        raise ValueError("Partial sensitivity results do not contain task_id")
    fault_counts = fault_rows.groupby("task_id").size()
    run_counts = run_rows.groupby("task_id").agg(
        rows=("run_index", "size"), unique_runs=("run_index", "nunique")
    )
    return {
        str(item)
        for item, count in fault_counts.items()
        if count == 1
        and item in run_counts.index
        and int(run_counts.loc[item, "rows"]) == expected_runs
        and int(run_counts.loc[item, "unique_runs"]) == expected_runs
    }


def retain_completed(frame: pd.DataFrame, completed: set[str]) -> pd.DataFrame:
    if frame.empty or not completed:
        return frame.iloc[0:0].copy()
    return frame[frame.task_id.astype(str).isin(completed)].copy()


def save_partial(output: Path, fault_rows: list[dict], run_rows: list[dict]) -> None:
    pd.DataFrame(fault_rows).to_csv(output / "SENSITIVITY_FAULT_RESULTS.partial.csv", index=False)
    pd.DataFrame(run_rows).to_csv(output / "SENSITIVITY_RUN_RESULTS.partial.csv", index=False)


def load_models(
    config: dict,
    mean: np.ndarray,
    std: np.ndarray,
    device: torch.device,
) -> dict[ModelKey, torch.nn.Module]:
    models: dict[ModelKey, torch.nn.Module] = {}
    checkpoint_root = resolve(config["paths"]["checkpoints"])
    for architecture in config["architectures"]:
        for seed in config["seeds"]:
            cp_path = (
                checkpoint_root
                / str(architecture)
                / f"reinartz_f1_seed_{int(seed)}.pt"
            )
            payload = torch.load(cp_path, map_location="cpu", weights_only=False)
            cp_mean = np.asarray(payload["mean"], dtype=np.float32)
            cp_std = np.asarray(payload["std"], dtype=np.float32)
            if not (np.allclose(mean, cp_mean) and np.allclose(std, cp_std)):
                raise ValueError(f"Scaler mismatch in {cp_path}")
            cp_config = payload["config"]
            model = MODEL_CLASSES[str(architecture)](
                52, int(cp_config["hidden_dim"]), int(cp_config["layers"])
            )
            model.load_state_dict(payload["state_dict"])
            model.to(device).eval()
            models[(str(architecture), int(seed))] = model
    return models


def score_models_per_draw(
    models: dict[ModelKey, torch.nn.Module],
    features: np.ndarray,
    run_ids: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
    loo_weights: np.ndarray,
    residual_bank: np.ndarray,
    mode: str,
    channel: int | None,
    start: int,
    end: int,
    window: int,
    device: torch.device,
    batch_size: int,
    run_batch_size: int,
    max_draws: int,
    residual_block_length: int,
) -> dict[ModelKey, np.ndarray]:
    if max_draws < 1:
        raise ValueError("max_draws must be at least one")
    score_blocks: dict[ModelKey, list[np.ndarray]] = {key: [] for key in models}
    unused_weights = np.empty((0, 0), dtype=np.float32)
    with torch.inference_mode():
        for run_offset in range(0, len(run_ids), run_batch_size):
            run_block = run_ids[run_offset : run_offset + run_batch_size]
            x_rows: list[np.ndarray] = []
            y_rows: list[np.ndarray] = []
            draws = max_draws if mode == "loo_sample" else 1
            for run in run_block:
                array = np.asarray(features[int(run)], dtype=np.float32)
                for draw in range(draws):
                    rng = np.random.default_rng(
                        20260821 + int(run) * 1000 + int(channel or 0) * 10 + draw
                    )
                    x, y = make_windows(
                        array,
                        mean,
                        std,
                        unused_weights,
                        loo_weights,
                        residual_bank,
                        mode,
                        channel,
                        start,
                        end,
                        window,
                        rng,
                        residual_block_length,
                    )
                    x_rows.append(x)
                    y_rows.append(y)
            x_block = np.concatenate(x_rows)
            y_block = np.concatenate(y_rows)
            model_scores: dict[ModelKey, list[np.ndarray]] = {key: [] for key in models}
            for offset in range(0, len(x_block), batch_size):
                xb = torch.from_numpy(x_block[offset : offset + batch_size]).to(device)
                yb = torch.from_numpy(y_block[offset : offset + batch_size]).to(device)
                for key, model in models.items():
                    residual = model(xb) - yb
                    model_scores[key].append(
                        torch.mean(torch.abs(residual), dim=1).cpu().numpy()
                    )
            for key, blocks in model_scores.items():
                scores = np.concatenate(blocks).reshape(len(run_block), draws, -1)
                score_blocks[key].append(scores)
    return {key: np.concatenate(blocks, axis=0) for key, blocks in score_blocks.items()}


def append_metric_rows(
    fault_rows: list[dict],
    run_rows: list[dict],
    architecture: str,
    seed: int,
    condition: str,
    mode: str,
    channel: int | None,
    block_length: int | None,
    draws: int,
    threshold: float,
    scores: np.ndarray,
    test: pd.DataFrame,
    config: dict,
) -> str:
    new_faults, new_runs = metric_rows(
        architecture,
        seed,
        condition,
        mode,
        channel,
        threshold,
        scores,
        test,
        int(config["evaluation_sample_start"]),
        int(config["evaluation_sample_end"]),
        int(config["fault_onset"]),
        int(config["alarm_consecutive"]),
    )
    if len(new_faults) != 1:
        raise AssertionError(f"Expected one fault row, found {len(new_faults)}")
    fault_id = int(new_faults[0]["fault_id"])
    identifier = task_id(
        architecture, seed, fault_id, channel, block_length, draws
    )
    common = {
        "task_id": identifier,
        "block_length": block_length,
        "draws": draws,
    }
    for row in new_faults:
        row.update(common)
    for row in new_runs:
        row.update(common)
    fault_rows.extend(new_faults)
    run_rows.extend(new_runs)
    return identifier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="configs/architecture_chum_sensitivity.yaml"
    )
    args = parser.parse_args()

    config_path = resolve(args.config)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config_sha256 = hashlib.sha256(config_path.read_bytes()).hexdigest()
    output = resolve(config["paths"]["output"])
    output.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(output / "SENSITIVITY_RUN.log", encoding="utf-8"),
        ],
    )

    device_name = str(config["device"])
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    device = torch.device(device_name if torch.cuda.is_available() else "cpu")

    features = np.load(resolve(config["paths"]["cache"]) / "features.npy", mmap_mode="r")
    split = pd.read_csv(resolve(config["paths"]["split"]))
    validation = split[split.split == "validation"].sort_values("run_index").reset_index(drop=True)
    selected_faults = sorted({int(cell["fault_id"]) for cell in config["primary_cells"]})
    test = split[
        (split.split == "test") & split.fault_id.astype(int).isin(selected_faults)
    ].sort_values(["fault_id", "run_index"]).reset_index(drop=True)
    scaler = pd.read_csv(resolve(config["paths"]["scaler"]))
    mean = scaler["mean"].to_numpy(np.float32)
    std = scaler["std"].to_numpy(np.float32)
    loo_weights = np.load(resolve(config["paths"]["loo_imputer_weights"]))
    residual_bank = np.load(
        resolve(config["paths"]["loo_residual_bank"]), mmap_mode="r"
    )

    if features.ndim != 3 or features.shape[2] != 52:
        raise ValueError(f"Expected features [runs, samples, 52], got {features.shape}")
    if loo_weights.shape != (94, 11):
        raise ValueError(f"Expected LOO weights (94, 11), got {loo_weights.shape}")
    if residual_bank.ndim != 3 or residual_bank.shape[1:] != (598, 11):
        raise ValueError(f"Unexpected residual bank shape: {residual_bank.shape}")
    if test.groupby("fault_id").size().nunique() != 1:
        raise ValueError("Locked primary faults must have equal test-run counts")
    expected_runs = int(test.groupby("fault_id").size().iloc[0])

    partial_fault = output / "SENSITIVITY_FAULT_RESULTS.partial.csv"
    partial_run = output / "SENSITIVITY_RUN_RESULTS.partial.csv"
    existing_faults = pd.read_csv(partial_fault) if partial_fault.exists() else pd.DataFrame()
    existing_runs = pd.read_csv(partial_run) if partial_run.exists() else pd.DataFrame()
    completed = completed_task_ids(existing_faults, existing_runs, expected_runs)
    existing_faults = retain_completed(existing_faults, completed)
    existing_runs = retain_completed(existing_runs, completed)
    fault_rows = existing_faults.to_dict("records")
    run_rows = existing_runs.to_dict("records")

    models = load_models(config, mean, std, device)
    all_expected = expected_task_ids(config)
    logging.info(
        "sensitivity tasks completed=%d total=%d device=%s",
        len(completed & all_expected),
        len(all_expected),
        device,
    )

    original_missing = {
        key
        for key in models
        if any(
            task_id(key[0], key[1], fault, None, None, 1) not in completed
            for fault in selected_faults
        )
    }
    if original_missing:
        active_models = {key: models[key] for key in original_missing}
        validation_scores = score_models_per_draw(
            active_models,
            features,
            validation.run_index.to_numpy(),
            mean,
            std,
            loo_weights,
            residual_bank,
            "original",
            None,
            int(config["evaluation_sample_start"]),
            int(config["fault_onset"]) - 1,
            int(config["window"]),
            device,
            int(config["batch_size"]),
            int(config["run_batch_size"]),
            1,
            int(config["window"]),
        )
        test_scores = score_models_per_draw(
            active_models,
            features,
            test.run_index.to_numpy(),
            mean,
            std,
            loo_weights,
            residual_bank,
            "original",
            None,
            int(config["evaluation_sample_start"]),
            int(config["evaluation_sample_end"]),
            int(config["window"]),
            device,
            int(config["batch_size"]),
            int(config["run_batch_size"]),
            1,
            int(config["window"]),
        )
        for key in sorted(active_models):
            architecture, seed = key
            threshold = float(
                np.percentile(
                    validation_scores[key][:, 0, :],
                    float(config["threshold_percentile"]),
                )
            )
            for fault_id in selected_faults:
                identifier = task_id(architecture, seed, fault_id, None, None, 1)
                if identifier in completed:
                    continue
                positions = test.index[test.fault_id.astype(int) == fault_id].to_numpy()
                test_fault = test.iloc[positions].reset_index(drop=True)
                completed.add(
                    append_metric_rows(
                        fault_rows,
                        run_rows,
                        architecture,
                        seed,
                        "original",
                        "original",
                        None,
                        None,
                        1,
                        threshold,
                        test_scores[key][positions, 0, :],
                        test_fault,
                        config,
                    )
                )
            save_partial(output, fault_rows, run_rows)

    draw_settings = sorted({int(value) for value in config["conditional_sample_draws"]})
    for cell in config["primary_cells"]:
        fault_id = int(cell["fault_id"])
        channel = int(cell["channel"])
        test_fault = test[test.fault_id.astype(int) == fault_id].reset_index(drop=True)
        for block_length in config["residual_block_lengths"]:
            block_length = int(block_length)
            missing_by_model: dict[ModelKey, list[int]] = {}
            for key in models:
                missing = [
                    draws
                    for draws in draw_settings
                    if task_id(
                        key[0], key[1], fault_id, channel, block_length, draws
                    )
                    not in completed
                ]
                if missing:
                    missing_by_model[key] = missing
            if not missing_by_model:
                continue
            active_models = {key: models[key] for key in missing_by_model}
            max_draws = max(max(values) for values in missing_by_model.values())
            logging.info(
                "cell F%d/XMV%d block=%d active_models=%d max_draws=%d",
                fault_id,
                channel,
                block_length,
                len(active_models),
                max_draws,
            )
            validation_scores = score_models_per_draw(
                active_models,
                features,
                validation.run_index.to_numpy(),
                mean,
                std,
                loo_weights,
                residual_bank,
                "loo_sample",
                channel,
                int(config["evaluation_sample_start"]),
                int(config["fault_onset"]) - 1,
                int(config["window"]),
                device,
                int(config["batch_size"]),
                int(config["run_batch_size"]),
                max_draws,
                block_length,
            )
            test_scores = score_models_per_draw(
                active_models,
                features,
                test_fault.run_index.to_numpy(),
                mean,
                std,
                loo_weights,
                residual_bank,
                "loo_sample",
                channel,
                int(config["evaluation_sample_start"]),
                int(config["evaluation_sample_end"]),
                int(config["window"]),
                device,
                int(config["batch_size"]),
                int(config["run_batch_size"]),
                max_draws,
                block_length,
            )
            for key in sorted(active_models):
                architecture, seed = key
                for draws in missing_by_model[key]:
                    condition = f"loo_sample_XMV_{channel:02d}_B{block_length:02d}_D{draws:02d}"
                    validation_mean = validation_scores[key][:, :draws, :].mean(axis=1)
                    threshold = float(
                        np.percentile(
                            validation_mean, float(config["threshold_percentile"])
                        )
                    )
                    test_mean = test_scores[key][:, :draws, :].mean(axis=1)
                    completed.add(
                        append_metric_rows(
                            fault_rows,
                            run_rows,
                            architecture,
                            seed,
                            condition,
                            "loo_sample",
                            channel,
                            block_length,
                            draws,
                            threshold,
                            test_mean,
                            test_fault,
                            config,
                        )
                    )
            save_partial(output, fault_rows, run_rows)
            logging.info(
                "progress completed=%d/%d", len(completed & all_expected), len(all_expected)
            )

    fault_frame = pd.DataFrame(fault_rows).sort_values(
        ["architecture", "seed", "fault_id", "mode", "channel", "block_length", "draws"],
        na_position="first",
    )
    run_frame = pd.DataFrame(run_rows).sort_values(
        [
            "architecture",
            "seed",
            "fault_id",
            "mode",
            "channel",
            "block_length",
            "draws",
            "run_index",
        ],
        na_position="first",
    )
    fault_frame.to_csv(output / "SENSITIVITY_FAULT_RESULTS.csv", index=False)
    run_frame.to_csv(output / "SENSITIVITY_RUN_RESULTS.csv", index=False)
    final_completed = completed_task_ids(fault_frame, run_frame, expected_runs)
    ending_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
    manifest = {
        "status": (
            "CONFIG_CHANGED_DURING_RUN"
            if ending_hash != config_sha256
            else (
                "COMPLETE_FULL_CONFIG"
                if all_expected.issubset(final_completed)
                else "INCOMPLETE"
            )
        ),
        "config": str(config_path),
        "config_sha256": config_sha256,
        "config_sha256_at_end": ending_hash,
        "device": str(device),
        "expected_tasks": len(all_expected),
        "completed_tasks": len(all_expected & final_completed),
        "fault_rows": len(fault_frame),
        "run_rows": len(run_frame),
        "test_runs_per_fault": expected_runs,
        "models": [f"{architecture}/seed-{seed}" for architecture, seed in sorted(models)],
        "primary_cells": config["primary_cells"],
        "residual_block_lengths": config["residual_block_lengths"],
        "conditional_sample_draws": config["conditional_sample_draws"],
    }
    (output / "SENSITIVITY_RUN_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
