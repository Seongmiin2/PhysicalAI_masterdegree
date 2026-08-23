from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]


def attach_deltas(frame: pd.DataFrame) -> pd.DataFrame:
    keys = ["architecture", "seed", "fault_id"]
    original = frame.loc[
        frame["mode"] == "original", keys + ["auroc", "auprc", "pre_fpr"]
    ].rename(
        columns={
            "auroc": "original_auroc",
            "auprc": "original_auprc",
            "pre_fpr": "original_pre_fpr",
        }
    )
    perturbed = frame.loc[frame["mode"] == "loo_sample"].copy()
    merged = perturbed.merge(original, on=keys, how="left", validate="many_to_one")
    if merged.original_auroc.isna().any():
        raise ValueError("Missing original baseline for sensitivity result")
    merged["delta_auroc"] = merged.original_auroc - merged.auroc
    merged["delta_auprc"] = merged.original_auprc - merged.auprc
    merged["delta_pre_fpr"] = merged.pre_fpr - merged.original_pre_fpr
    return merged


def hierarchical_intervals(run_frame: pd.DataFrame, repeats: int) -> pd.DataFrame:
    keys = ["architecture", "seed", "fault_id", "run_index"]
    original = run_frame.loc[
        run_frame["mode"] == "original", keys + ["auroc", "auprc"]
    ].rename(columns={"auroc": "original_auroc", "auprc": "original_auprc"})
    paired = run_frame.loc[run_frame["mode"] == "loo_sample"].merge(
        original, on=keys, how="left", validate="many_to_one"
    )
    paired["run_delta_auroc"] = paired.original_auroc - paired.auroc
    paired["run_delta_auprc"] = paired.original_auprc - paired.auprc
    group_keys = [
        "architecture",
        "fault_id",
        "channel",
        "block_length",
        "draws",
    ]
    rng = np.random.default_rng(20260823)
    rows: list[dict] = []
    for group_key, group in paired.groupby(group_keys, sort=True):
        by_seed = [
            seed_frame.sort_values("run_index")
            for _, seed_frame in group.groupby("seed", sort=True)
        ]
        if len(by_seed) != 5:
            raise ValueError(f"Expected five seeds in {group_key}, found {len(by_seed)}")
        run_counts = {len(seed_frame) for seed_frame in by_seed}
        if len(run_counts) != 1:
            raise ValueError(f"Unequal test-run counts in {group_key}: {run_counts}")
        auroc = np.stack(
            [seed_frame.run_delta_auroc.to_numpy(float) for seed_frame in by_seed]
        )
        auprc = np.stack(
            [seed_frame.run_delta_auprc.to_numpy(float) for seed_frame in by_seed]
        )
        seed_draws = rng.integers(0, len(by_seed), size=(repeats, len(by_seed)))
        run_draws = rng.integers(
            0, auroc.shape[1], size=(repeats, len(by_seed), auroc.shape[1])
        )
        auroc_boot = auroc[seed_draws[:, :, None], run_draws].mean(axis=(1, 2))
        auprc_boot = auprc[seed_draws[:, :, None], run_draws].mean(axis=(1, 2))
        architecture, fault_id, channel, block_length, draws = group_key
        rows.append(
            {
                "architecture": architecture,
                "fault_id": int(fault_id),
                "channel": int(channel),
                "block_length": int(block_length),
                "draws": int(draws),
                "run_delta_auroc_mean": float(group.run_delta_auroc.mean()),
                "run_delta_auroc_ci_low": float(np.quantile(auroc_boot, 0.025)),
                "run_delta_auroc_ci_high": float(np.quantile(auroc_boot, 0.975)),
                "run_delta_auprc_mean": float(group.run_delta_auprc.mean()),
                "run_delta_auprc_ci_low": float(np.quantile(auprc_boot, 0.025)),
                "run_delta_auprc_ci_high": float(np.quantile(auprc_boot, 0.975)),
            }
        )
    return pd.DataFrame(rows)


def build_architecture_cell_summary(
    settings: pd.DataFrame, rule: dict
) -> pd.DataFrame:
    group_keys = ["architecture", "fault_id", "channel"]
    summary = (
        settings.groupby(group_keys, as_index=False)
        .agg(
            settings=("draws", "size"),
            positive_settings=("direction_positive", "sum"),
            material_settings=("material_effect", "sum"),
            seed_stable_settings=("seed_stable", "sum"),
            fpr_guardrail_settings=("fpr_guardrail_pass", "sum"),
            ci_positive_settings=("ci_positive", "sum"),
            strict_pass_settings=("setting_pass", "sum"),
            min_delta_auroc=("mean_delta_auroc", "min"),
            median_delta_auroc=("mean_delta_auroc", "median"),
            max_delta_auroc=("mean_delta_auroc", "max"),
            worst_abs_fpr_shift=("max_abs_pre_fpr_shift", "max"),
        )
    )
    reference = settings[
        (settings.block_length == 20) & (settings.draws == 3)
    ][group_keys + ["mean_delta_auroc", "setting_pass"]].rename(
        columns={
            "mean_delta_auroc": "reference_delta_auroc",
            "setting_pass": "reference_setting_pass",
        }
    )
    summary = summary.merge(reference, on=group_keys, how="left", validate="one_to_one")
    summary["architecture_cell_robust"] = (
        (summary.positive_settings >= int(rule["required_positive_settings"]))
        & (summary.material_settings >= int(rule["required_material_settings"]))
        & (summary.seed_stable_settings >= int(rule["required_seed_stable_settings"]))
        & (
            summary.fpr_guardrail_settings
            >= int(rule["required_fpr_guardrail_settings"])
        )
        & (summary.ci_positive_settings >= int(rule["required_ci_positive_settings"]))
        & summary.reference_setting_pass.fillna(False)
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", default="configs/architecture_chum_sensitivity.yaml"
    )
    args = parser.parse_args()
    config_path = (ROOT / args.config).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    output = (ROOT / config["paths"]["output"]).resolve()
    manifest = json.loads(
        (output / "SENSITIVITY_RUN_MANIFEST.json").read_text(encoding="utf-8")
    )
    if manifest.get("status") != "COMPLETE_FULL_CONFIG":
        raise RuntimeError(
            "Sensitivity analysis requires a complete run; "
            f"found {manifest.get('status')!r}"
        )

    fault_frame = pd.read_csv(output / "SENSITIVITY_FAULT_RESULTS.csv")
    run_frame = pd.read_csv(output / "SENSITIVITY_RUN_RESULTS.csv")
    cells = attach_deltas(fault_frame)
    cells.to_csv(output / "SENSITIVITY_CELL_RESULTS.csv", index=False)
    rule = config["decision_rule"]
    group_keys = [
        "architecture",
        "fault_id",
        "channel",
        "block_length",
        "draws",
    ]
    settings = (
        cells.groupby(group_keys, as_index=False)
        .agg(
            mean_delta_auroc=("delta_auroc", "mean"),
            median_delta_auroc=("delta_auroc", "median"),
            min_delta_auroc=("delta_auroc", "min"),
            mean_delta_auprc=("delta_auprc", "mean"),
            positive_auroc_seeds=("delta_auroc", lambda values: int(np.sum(values > 0))),
            max_abs_pre_fpr_shift=(
                "delta_pre_fpr",
                lambda values: float(np.max(np.abs(values))),
            ),
        )
    )
    intervals = hierarchical_intervals(
        run_frame, repeats=int(config["bootstrap_repeats"])
    )
    intervals.to_csv(output / "SENSITIVITY_RUN_CI.csv", index=False)
    settings = settings.merge(intervals, on=group_keys, how="left", validate="one_to_one")
    settings["direction_positive"] = settings.mean_delta_auroc > 0
    settings["material_effect"] = (
        settings.mean_delta_auroc >= float(rule["material_delta_auroc"])
    )
    settings["seed_stable"] = (
        settings.positive_auroc_seeds >= int(rule["positive_seeds"])
    )
    settings["fpr_guardrail_pass"] = (
        settings.max_abs_pre_fpr_shift <= float(rule["fpr_guardrail"])
    )
    settings["ci_positive"] = settings.run_delta_auroc_ci_low > 0
    settings["setting_pass"] = (
        settings.material_effect
        & settings.seed_stable
        & settings.fpr_guardrail_pass
        & settings.ci_positive
    )
    settings.to_csv(output / "SENSITIVITY_SETTING_SUMMARY.csv", index=False)

    architecture_cells = build_architecture_cell_summary(settings, rule)
    architecture_cells.to_csv(
        output / "SENSITIVITY_ARCHITECTURE_CELL_SUMMARY.csv", index=False
    )
    consensus = (
        architecture_cells.groupby(["fault_id", "channel"], as_index=False)
        .agg(
            robust_architecture_count=("architecture_cell_robust", "sum"),
            min_delta_auroc_across_settings=("min_delta_auroc", "min"),
            median_delta_auroc_across_architectures=("median_delta_auroc", "median"),
            worst_abs_fpr_shift=("worst_abs_fpr_shift", "max"),
        )
    )
    consensus["two_architecture_robust"] = consensus.robust_architecture_count == 2
    consensus.to_csv(output / "SENSITIVITY_CONSENSUS.csv", index=False)
    consensus_cells = int(consensus.two_architecture_robust.sum())
    decision = (
        "PASS"
        if consensus_cells >= int(rule["required_consensus_cells"])
        else "MODIFY"
    )

    report = [
        "# CHUM Primary-Cell Sensitivity Report",
        "",
        "## Decision",
        "",
        f"**{decision}**: `{consensus_cells}/{len(consensus)}` locked primary cells retained the preregistered two-architecture robustness rule across residual block lengths 5/10/20 and conditional draw counts 1/3/10.",
        "",
        "## Locked Decision Rule",
        "",
        "Each architecture-cell must keep positive mean delta AUROC in 9/9 settings; material delta AUROC (>=0.02), >=4/5 positive seeds, and positive hierarchical run CI in at least 8/9 settings; the absolute pre-fault FPR shift must remain <=0.005 in 9/9 settings; and the reference setting block=20/draws=3 must pass all setting-level gates. Overall PASS requires both architectures to pass for all four locked cells.",
        "",
        "## Architecture-Cell Robustness",
        "",
        architecture_cells.round(6).to_markdown(index=False),
        "",
        "## Cross-Architecture Consensus",
        "",
        consensus.round(6).to_markdown(index=False),
        "",
        "## Interpretation Boundary",
        "",
        "This no-retraining sensitivity test checks whether the CHUM conclusion depends on two stochastic replacement hyperparameters. It does not establish a causal controller effect, a physical root cause, or independence beyond the fixed TEP test distribution.",
    ]
    (output / "CHUM_PRIMARY_SENSITIVITY_REPORT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    (output / "SENSITIVITY_DECISION.json").write_text(
        json.dumps(
            {
                "status": "COMPLETE",
                "decision": decision,
                "consensus_cells": consensus_cells,
                "required_consensus_cells": int(rule["required_consensus_cells"]),
                "decision_rule": rule,
                "bootstrap_repeats": int(config["bootstrap_repeats"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
