from __future__ import annotations

import argparse
import io
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "bc6166f"
LOCKED_CELLS = {(4, 10), (19, 7), (19, 8), (25, 2)}
ARCHITECTURES = ("tcn", "transformer")


def historical_csv(path: str) -> pd.DataFrame:
    completed = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return pd.read_csv(io.BytesIO(completed.stdout))


def bh_adjust(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    ranked = p_values[order] * len(p_values) / np.arange(1, len(p_values) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted = np.empty_like(ranked)
    adjusted[order] = np.minimum(ranked, 1.0)
    return adjusted


def eligible_cells(summary: pd.DataFrame) -> pd.DataFrame:
    primary = summary[
        (summary["mode"] == "loo_sample")
        & summary["architecture"].isin(ARCHITECTURES)
        & summary["imputer_reliable"].fillna(False).astype(bool)
    ].copy()
    counts = (
        primary.groupby(["fault_id", "channel"])["architecture"]
        .nunique()
        .rename("architecture_count")
        .reset_index()
    )
    cells = counts[counts.architecture_count == len(ARCHITECTURES)].copy()
    cells["fault_id"] = cells.fault_id.astype(int)
    cells["channel"] = cells.channel.astype(int)
    return cells.sort_values(["fault_id", "channel"]).reset_index(drop=True)


def selection_manifest(summary: pd.DataFrame, imputer: pd.DataFrame) -> dict:
    cells = eligible_cells(summary)
    primary_validation = imputer[imputer.method == "loo_residual_sample"].copy()
    primary_validation["constant"] = primary_validation.observed_std.fillna(0) <= 1e-12
    primary_validation["reliable"] = (
        (~primary_validation.constant)
        & primary_validation.std_ratio.between(0.75, 1.25)
        & (primary_validation.wasserstein <= 0.1)
        & (primary_validation.ks_statistic <= 0.1)
        & ((primary_validation.observed_lag1 - primary_validation.predicted_lag1).abs() <= 0.2)
    )
    reliable = sorted(primary_validation.loc[primary_validation.reliable, "channel"].astype(int))
    constants = sorted(primary_validation.loc[primary_validation.constant, "channel"].astype(int))
    quality_failed = sorted(
        primary_validation.loc[
            ~primary_validation.reliable & ~primary_validation.constant, "channel"
        ].astype(int)
    )
    faults = sorted(cells.fault_id.unique().tolist())
    raw_channels = sorted(primary_validation.channel.astype(int).unique().tolist())
    return {
        "status": "COMPLETE_RESTORED_FROM_GIT_EVIDENCE",
        "source_commit": SOURCE_COMMIT,
        "source_cell_results": "outputs/architecture_chum_g3/G3_CELL_RESULTS.csv",
        "primary_mode": "loo_sample",
        "consensus_architectures": list(ARCHITECTURES),
        "evaluated_faults": faults,
        "evaluated_fault_count": len(faults),
        "archive_xmv_channels": raw_channels,
        "archive_xmv_count": len(raw_channels),
        "missing_archive_channel": 12,
        "constant_channels": constants,
        "nonconstant_channel_count": len(raw_channels) - len(constants),
        "quality_gate": {
            "method": "loo_residual_sample",
            "rules": {
                "observed_std": "> 1e-12",
                "std_ratio": "0.75 <= value <= 1.25",
                "wasserstein": "<= 0.1",
                "ks_statistic": "<= 0.1",
                "absolute_lag1_difference": "<= 0.2",
            },
            "reliable_channels": reliable,
            "reliable_channel_count": len(reliable),
            "failed_nonconstant_channels": quality_failed,
            "failed_constant_channels": constants,
            "failed_channel_count": len(raw_channels) - len(reliable),
        },
        "raw_evaluated_cell_count": len(faults) * len(raw_channels),
        "primary_candidate_cell_formula": f"{len(faults)} faults x {len(reliable)} reliable channels",
        "primary_candidate_cell_count": len(cells),
        "excluded_raw_cell_count": len(faults) * (len(raw_channels) - len(reliable)),
        "locked_cells": [
            {"fault_id": fault, "channel": channel}
            for fault, channel in sorted(LOCKED_CELLS)
        ],
        "locked_cell_count": len(LOCKED_CELLS),
    }


def permutation_results(
    run_frame: pd.DataFrame,
    summary: pd.DataFrame,
    repeats: int,
    random_seed: int,
) -> pd.DataFrame:
    cells = eligible_cells(summary)
    valid_pairs = set(zip(cells.fault_id, cells.channel))
    original = run_frame.loc[
        (run_frame["mode"] == "original") & run_frame.architecture.isin(ARCHITECTURES),
        ["architecture", "seed", "fault_id", "run_index", "auroc"],
    ].drop_duplicates(["architecture", "seed", "fault_id", "run_index"])
    original = original.rename(columns={"auroc": "original_auroc"})
    perturbed = run_frame.loc[
        (run_frame["mode"] == "loo_sample") & run_frame.architecture.isin(ARCHITECTURES)
    ].copy()
    perturbed["channel"] = perturbed.channel.astype(int)
    perturbed = perturbed[
        [(int(f), int(c)) in valid_pairs for f, c in zip(perturbed.fault_id, perturbed.channel)]
    ]
    paired = perturbed.merge(
        original,
        on=["architecture", "seed", "fault_id", "run_index"],
        how="left",
        validate="many_to_one",
    )
    if paired.original_auroc.isna().any():
        raise ValueError("Missing original run metric while constructing paired deltas")
    paired["run_delta_auroc"] = paired.original_auroc - paired.auroc

    cluster = (
        paired.groupby(["fault_id", "channel", "run_index"], as_index=False)
        .agg(
            run_cluster_delta_auroc=("run_delta_auroc", "mean"),
            architecture_seed_observations=("run_delta_auroc", "size"),
        )
        .sort_values(["fault_id", "channel", "run_index"])
    )
    groups = list(cluster.groupby(["fault_id", "channel"], sort=True))
    if len(groups) != len(cells):
        raise ValueError(f"Expected {len(cells)} candidate groups, found {len(groups)}")
    if any(len(group) != 20 for _, group in groups):
        raise ValueError("Every candidate cell must contain exactly 20 held-out run clusters")
    if set(cluster.architecture_seed_observations.unique()) != {10}:
        raise ValueError("Each run cluster must average two architectures x five seeds")

    values = np.stack(
        [group.run_cluster_delta_auroc.to_numpy(float) for _, group in groups]
    )
    observed = values.mean(axis=1)
    rng = np.random.default_rng(random_seed)
    exceed = np.zeros(len(groups), dtype=np.int64)
    batch_size = 10_000
    for start in range(0, repeats, batch_size):
        size = min(batch_size, repeats - start)
        signs = rng.integers(0, 2, size=(size, 20), dtype=np.int8) * 2 - 1
        null_means = signs.astype(np.float64) @ values.T / 20.0
        exceed += np.sum(null_means >= observed[None, :], axis=0)
    p_values = (exceed + 1) / (repeats + 1)
    q_values = bh_adjust(p_values)

    summary_primary = summary[
        (summary["mode"] == "loo_sample") & summary.architecture.isin(ARCHITECTURES)
    ].copy()
    rows = []
    for index, ((fault, channel), group) in enumerate(groups):
        arch = summary_primary[
            (summary_primary.fault_id == fault) & (summary_primary.channel == channel)
        ]
        rows.append(
            {
                "fault_id": int(fault),
                "channel": int(channel),
                "candidate_family": "28_faults_x_8_quality_gated_channels",
                "test_unit": "20_paired_test_run_clusters",
                "architectures": "tcn,transformer",
                "seeds": "42,43,44,45,46",
                "observed_mean_delta_auroc": observed[index],
                "positive_run_clusters": int(np.sum(values[index] > 0)),
                "permutation_repeats": repeats,
                "p_value_one_sided": p_values[index],
                "bh_q_value": q_values[index],
                "bh_pass_q_0_05": bool(q_values[index] <= 0.05),
                "bh_pass_q_0_10": bool(q_values[index] <= 0.10),
                "both_architectures_positive_5_of_5": bool(
                    len(arch) == 2
                    and (arch.positive_auroc_seeds == 5).all()
                    and (arch.mean_delta_auroc > 0).all()
                ),
                "both_architectures_stable_material": bool(
                    len(arch) == 2 and arch.stable_material.astype(bool).all()
                ),
                "locked_cell": (int(fault), int(channel)) in LOCKED_CELLS,
            }
        )
    return pd.DataFrame(rows).sort_values(["p_value_one_sided", "fault_id", "channel"])


def three_architecture_comparison(summary: pd.DataFrame, gru_path: Path) -> pd.DataFrame:
    locked_mask = np.array(
        [
            (int(fault), int(channel)) in LOCKED_CELLS
            for fault, channel in zip(summary.fault_id, summary.channel)
        ],
        dtype=bool,
    )
    locked_summary = summary[
        (summary["mode"] == "loo_sample")
        & summary.architecture.isin(ARCHITECTURES)
        & locked_mask
    ]
    rows = []
    for item in locked_summary.itertuples(index=False):
        rows.append(
            {
                "architecture": item.architecture,
                "fault_id": int(item.fault_id),
                "channel": int(item.channel),
                "evaluation_condition": "loo_residual_sample",
                "seeds": "42,43,44,45,46",
                "mean_delta_auroc": item.mean_delta_auroc,
                "min_delta_auroc": item.min_delta_auroc,
                "mean_delta_auprc": item.mean_delta_auprc,
                "positive_auroc_seeds": int(item.positive_auroc_seeds),
                "imputer_quality_gate_pass": bool(item.imputer_reliable),
                "run_delta_auroc_ci_low": item.run_delta_auroc_ci_low,
                "run_delta_auroc_ci_high": item.run_delta_auroc_ci_high,
                "raw_direction": "POSITIVE",
                "consensus_included": True,
                "exclusion_reason": "",
                "source": f"{SOURCE_COMMIT}:G3_CELL_SUMMARY.csv",
            }
        )
    gru = pd.read_csv(gru_path)
    gru = gru[gru.gru_mode == "conditional"]
    for item in gru.itertuples(index=False):
        rows.append(
            {
                "architecture": "gru",
                "fault_id": int(item.fault_id),
                "channel": int(item.xmv_channel),
                "evaluation_condition": "legacy_mean_conditional",
                "seeds": item.seeds,
                "mean_delta_auroc": item.mean_delta_auroc,
                "min_delta_auroc": item.min_delta_auroc,
                "mean_delta_auprc": item.mean_delta_auprc,
                "positive_auroc_seeds": int(item.positive_auroc_seeds),
                "imputer_quality_gate_pass": item.imputer_quality_gate_pass,
                "run_delta_auroc_ci_low": np.nan,
                "run_delta_auroc_ci_high": np.nan,
                "raw_direction": "POSITIVE",
                "consensus_included": False,
                "exclusion_reason": "different_imputation_and_no_hierarchical_run_ci",
                "source": f"{SOURCE_COMMIT}:GRU conditional evidence",
            }
        )
    return pd.DataFrame(rows).sort_values(["fault_id", "channel", "architecture"])


def multiplicity_report(results: pd.DataFrame, manifest: dict, repeats: int) -> str:
    locked = results[results.locked_cell]
    q05 = int(results.bh_pass_q_0_05.sum())
    q10 = int(results.bh_pass_q_0_10.sum())
    locked_q05 = int(locked.bh_pass_q_0_05.sum())
    locked_q10 = int(locked.bh_pass_q_0_10.sum())
    independent_probability = 0.5 ** (5 + 2 + 9)
    expected_false = manifest["primary_candidate_cell_count"] * independent_probability
    family_probability = 1 - (1 - independent_probability) ** manifest["primary_candidate_cell_count"]
    locked_table = locked[
        [
            "fault_id",
            "channel",
            "observed_mean_delta_auroc",
            "p_value_one_sided",
            "bh_q_value",
            "bh_pass_q_0_05",
            "bh_pass_q_0_10",
        ]
    ].sort_values(["fault_id", "channel"])
    locked_lines = [
        "| fault_id | channel | observed_mean_delta_auroc | p_value_one_sided | bh_q_value | bh_pass_q_0_05 | bh_pass_q_0_10 |",
        "|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for row in locked_table.itertuples(index=False):
        locked_lines.append(
            f"| {int(row.fault_id)} | {int(row.channel)} | "
            f"{row.observed_mean_delta_auroc:.6g} | {row.p_value_one_sided:.6g} | "
            f"{row.bh_q_value:.6g} | {row.bh_pass_q_0_05} | {row.bh_pass_q_0_10} |"
        )
    locked_markdown = "\n".join(locked_lines)
    return f"""# CHUM multiplicity report

## 분석 family와 분모

Primary family는 28개 fault와 LOO-residual imputer quality gate를 통과한
8개 channel의 Cartesian product인 **224개 candidate cell**이다. 원시
G3는 11개 archive channel, 즉 308개 cell을 모두 계산했지만 XMV5·XMV9는
상수이고 XMV4는 primary imputer quality gate를 통과하지 못해 confirmatory
family에서 제외했다. 제외 규칙은 효과크기가 아니라 대치 품질에만 근거한다.

## p-value와 BH-FDR

- 통계 단위: fault별 20개 held-out test run.
- 각 run에서 2 architectures × 5 seeds의 paired AUROC loss를 평균해 하나의
  run-cluster delta를 만들었다.
- 귀무가설은 run-cluster delta의 부호가 대칭이라는 것이다.
- 대립가설은 conditional replacement가 AUROC를 낮춘다는 단측 방향이다.
- 고정 seed의 paired sign-flip permutation을 {repeats:,}회 시행하고 add-one
  보정을 적용했다.
- 224개 p-value 전체에 Benjamini–Hochberg를 한 번 적용했다.

q=0.05 생존 cell은 **{q05}/224**, q=0.10 생존 cell은 **{q10}/224**다.
기존 locked 4개 중 q=0.05 생존은 **{locked_q05}/4**, q=0.10 생존은
**{locked_q10}/4**다.

{locked_markdown}

이 검정은 fixed TEP test distribution의 run-level 안정성을 다룬다. 5개
model seed를 독립 데이터셋으로 세지 않으며, 물리적 인과효과를 검정하지
않는다.

## 3중 필터 결합 확률

Locked cell은 ① 5/5 seed 양의 방향, ② TCN·Transformer 2/2 architecture
양의 방향, ③ 9/9 sensitivity 설정 양의 방향을 동시에 만족했다. 각 표결을
독립이고 귀무가설 아래 양/음 확률이 1/2라고 두는 **설명용 근사**에서는

`P(pass) = 2^-(5+2+9) = {independent_probability:.10f}`

이고, 224개 후보의 기대 통과 위양성 수는 **{expected_false:.6f}**, 적어도
하나가 우연히 통과할 확률 근사는 **{family_probability:.6f}**다.

그러나 seed, architecture, sensitivity 설정은 같은 데이터와 학습 계보를
공유하므로 독립 가정은 강하다. sensitivity 9개를 완전 의존으로 축약하면
동일 계산은 `2^-(5+2+1) = {0.5 ** 8:.8f}`, 기대 위양성 수
**{manifest['primary_candidate_cell_count'] * (0.5 ** 8):.3f}**까지 커진다.
architecture와 sensitivity 의존성을 모두 무시하고 seed 방향만 남기면
기대 위양성 수는 `224 / 32 = 7.0`이다. 따라서 이 결합 확률은 BH-FDR을
대체하는 유의확률이 아니라, 반복 필터가 얼마나 엄격한지 보여 주는
민감도 설명으로만 사용한다.

## 재현

`python experiments/analyze_chum_multiplicity.py`

원자료는 Git evidence commit `{SOURCE_COMMIT}`의 G3 cell/run tables이며,
복원된 `G3_CELL_RESULTS.csv`의 SHA-256과 분모는
`G3_SELECTION_MANIFEST.json`에 기록된다.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--permutation-repeats", type=int, default=200_000)
    parser.add_argument("--random-seed", type=int, default=20260825)
    args = parser.parse_args()

    g3_output = ROOT / "outputs/architecture_chum_g3"
    multiplicity_output = ROOT / "outputs/chum_multiplicity"
    consensus_output = ROOT / "outputs/architecture_consensus"
    g3_output.mkdir(parents=True, exist_ok=True)
    multiplicity_output.mkdir(parents=True, exist_ok=True)
    consensus_output.mkdir(parents=True, exist_ok=True)

    restored = g3_output / "G3_CELL_RESULTS.csv"
    if not restored.exists():
        raise FileNotFoundError("Restore G3_CELL_RESULTS.csv from evidence commit first")
    restored_rows = len(pd.read_csv(restored))
    if restored_rows != 12_320:
        raise ValueError(f"Expected 12,320 restored G3 cell rows, found {restored_rows}")

    summary = historical_csv("outputs/architecture_chum_g3/G3_CELL_SUMMARY.csv")
    imputer = historical_csv("outputs/architecture_chum_g3/IMPUTER_VALIDATION.csv")
    run_frame = historical_csv("outputs/architecture_chum_g3/G3_RUN_RESULTS.csv")

    manifest = selection_manifest(summary, imputer)
    import hashlib

    manifest["restored_cell_rows"] = restored_rows
    manifest["restored_cell_sha256"] = hashlib.sha256(restored.read_bytes()).hexdigest()
    (g3_output / "G3_SELECTION_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    results = permutation_results(
        run_frame, summary, repeats=args.permutation_repeats, random_seed=args.random_seed
    )
    results.to_csv(multiplicity_output / "BH_FDR_RESULTS.csv", index=False)
    (multiplicity_output / "MULTIPLICITY_REPORT.md").write_text(
        multiplicity_report(results, manifest, args.permutation_repeats), encoding="utf-8"
    )

    comparison = three_architecture_comparison(
        summary, consensus_output / "GRU_CELL_RESULTS.csv"
    )
    comparison.to_csv(consensus_output / "THREE_ARCH_COMPARISON.csv", index=False)


if __name__ == "__main__":
    main()
