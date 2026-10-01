from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from src.experiments.reinartz_f0_f1 import binary_metrics
from src.models.reinartz_forecaster import GRUForecaster

LOGGER = logging.getLogger(__name__)
FAULTS = (4, 7, 19, 24, 25, 26)
ONSET_INDEX = 599  # zero-based index for documented sample 600
WINDOW = 20
PRE_SLICE = slice(399, ONSET_INDEX)   # samples 400..599
POST_SLICE = slice(ONSET_INDEX, 899)  # samples 600..899


def first_persistent(values: np.ndarray, threshold: float, start: int, consecutive: int = 3) -> float:
    exceed = values[start:] >= threshold
    hits = np.convolve(exceed.astype(np.int8), np.ones(consecutive, dtype=np.int8), mode="valid")
    found = np.flatnonzero(hits >= consecutive)
    return float(found[0]) if len(found) else float("nan")


def infer_scores(features: np.ndarray, runs: np.ndarray, checkpoint_path: Path, input_dim: int, device: torch.device, batch_size: int = 2048) -> np.ndarray:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config = checkpoint["config"]
    model = GRUForecaster(input_dim, int(config["hidden_dim"]), int(config["layers"]))
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device).eval()
    mean = np.asarray(checkpoint["mean"], dtype=np.float32)
    std = np.asarray(checkpoint["std"], dtype=np.float32)
    result = np.empty((len(runs), 2000 - WINDOW), dtype=np.float32)
    LOGGER.info("scoring %s on %s: runs=%d", checkpoint_path.name, device, len(runs))
    with torch.no_grad():
        for row, run in enumerate(runs):
            array = np.asarray(features[run, :, :input_dim], dtype=np.float32)
            windows = np.lib.stride_tricks.sliding_window_view(array, (WINDOW, input_dim))[: 2000 - WINDOW, 0]
            targets = np.asarray(features[run, WINDOW:, :41], dtype=np.float32)
            for start in range(0, len(windows), batch_size):
                end = min(start + batch_size, len(windows))
                x = (np.array(windows[start:end], copy=True) - mean[:input_dim]) / std[:input_dim]
                y = (targets[start:end] - mean[:41]) / std[:41]
                pred = model(torch.from_numpy(x).to(device))
                score = torch.mean(torch.abs(pred - torch.from_numpy(y).to(device)), dim=1)
                result[row, start:end] = score.cpu().numpy()
            if (row + 1) % 10 == 0 or row + 1 == len(runs):
                LOGGER.info("%s progress: %d/%d runs", checkpoint_path.stem, row + 1, len(runs))
    return result


def deviation_scores(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    baseline = z[:, PRE_SLICE, :].mean(axis=1, keepdims=True)
    level = np.sqrt(np.mean((z - baseline) ** 2, axis=2))
    delta = np.sqrt(np.mean(np.diff(z, axis=1, prepend=z[:, :1]) ** 2, axis=2))
    return level, delta


def best_lag(xmv_delta: np.ndarray, xmeas_delta: np.ndarray, window: slice) -> tuple[int, float]:
    x = xmv_delta[:, window].reshape(-1)
    y = xmeas_delta[:, window].reshape(-1)
    best = (0, -np.inf)
    for lag in range(-20, 21):
        if lag > 0:
            a, b = x[:-lag], y[lag:]
        elif lag < 0:
            a, b = x[-lag:], y[:lag]
        else:
            a, b = x, y
        corr = float(np.corrcoef(a, b)[0, 1]) if np.std(a) and np.std(b) else float("nan")
        if np.isfinite(corr) and corr > best[1]:
            best = (lag, corr)
    return best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="data/processed/reinartz_f0_f1")
    parser.add_argument("--split", default="artifacts/tables/reinartz_split_manifest.csv")
    parser.add_argument("--results", default="artifacts/tables/reinartz_f0_f1_results.csv")
    parser.add_argument("--output", default="artifacts/tables")
    parser.add_argument("--figures", default="artifacts/figures")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    output, figures = Path(args.output), Path(args.figures)
    output.mkdir(parents=True, exist_ok=True); figures.mkdir(parents=True, exist_ok=True)
    split = pd.read_csv(args.split)
    selected = split[(split["split"] == "test") & split["fault_id"].isin(FAULTS)].copy()
    selected = selected.sort_values(["fault_id", "run_index"])
    runs = selected["run_index"].to_numpy(dtype=int)
    fault_by_run = selected.set_index("run_index")["fault_id"].to_dict()
    features = np.load(Path(args.cache) / "features.npy", mmap_mode="r")
    checkpoint = torch.load("checkpoints/reinartz_f0_seed_42.pt", map_location="cpu", weights_only=False)
    mean, std = np.asarray(checkpoint["mean"]), np.asarray(checkpoint["std"])
    z = (np.asarray(features[runs], dtype=np.float32) - mean) / std
    xmeas_level, xmeas_delta = deviation_scores(z[:, :, :41])
    xmv_level, xmv_delta = deviation_scores(z[:, :, 41:])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    LOGGER.info("device=%s selected_test_runs=%d", device, len(runs))
    f0 = infer_scores(features, runs, Path("checkpoints/reinartz_f0_seed_42.pt"), 41, device)
    f1 = infer_scores(features, runs, Path("checkpoints/reinartz_f1_seed_42.pt"), 52, device)
    result_rows = pd.read_csv(args.results).set_index("variant")
    f0_threshold, f1_threshold = float(result_rows.loc["F0", "threshold"]), float(result_rows.loc["F1", "threshold"])

    rows, feature_rows, run_rows = [], [], []
    figure, axes = plt.subplots(3, 2, figsize=(14, 12), sharex=True)
    samples = np.arange(1, 2001)
    score_samples = np.arange(WINDOW + 1, 2001)
    for axis, fault in zip(axes.flat, FAULTS):
        idx = np.array([fault_by_run[run] == fault for run in runs])
        LOGGER.info("fault %d audit: runs=%d", fault, int(idx.sum()))
        xmv_pre_threshold = float(np.percentile(xmv_level[idx, PRE_SLICE], 99))
        xmeas_pre_threshold = float(np.percentile(xmeas_level[idx, PRE_SLICE], 99))
        labels = np.concatenate([np.zeros(idx.sum() * 200, dtype=np.int8), np.ones(idx.sum() * 300, dtype=np.int8)])
        xmv_eval = np.concatenate([xmv_level[idx, PRE_SLICE].reshape(-1), xmv_level[idx, POST_SLICE].reshape(-1)])
        xmv_delta_eval = np.concatenate([xmv_delta[idx, PRE_SLICE].reshape(-1), xmv_delta[idx, POST_SLICE].reshape(-1)])
        xmv_auc, xmv_auprc = binary_metrics(labels, xmv_eval)
        xmv_delta_auc, _ = binary_metrics(labels, xmv_delta_eval)
        pre_lag, pre_corr = best_lag(xmv_delta[idx], xmeas_delta[idx], slice(299, ONSET_INDEX))
        post_lag, post_corr = best_lag(xmv_delta[idx], xmeas_delta[idx], POST_SLICE)
        feature_shift = np.mean(np.abs(z[idx, ONSET_INDEX:ONSET_INDEX + 120, 41:] - z[idx, PRE_SLICE, 41:].mean(axis=1, keepdims=True)), axis=(0, 1))
        order = np.argsort(-feature_shift)
        top3_share = float(feature_shift[order[:3]].sum() / feature_shift.sum()) if feature_shift.sum() else 0.0
        for rank, feature_index in enumerate(order, start=1):
            feature_rows.append({"fault_id": fault, "rank": rank, "feature": f"XMV_{feature_index + 1:02d}", "mean_abs_shift_120": float(feature_shift[feature_index]), "share": float(feature_shift[feature_index] / feature_shift.sum()) if feature_shift.sum() else 0.0})

        f0_fault, f1_fault = f0[idx], f1[idx]
        fault_row_indices = np.flatnonzero(idx)
        f0_delays, f1_delays, xmv_delays, xmeas_delays = [], [], [], []
        for local, global_row in enumerate(fault_row_indices):
            f0_delay = first_persistent(f0[global_row], f0_threshold, ONSET_INDEX - WINDOW)
            f1_delay = first_persistent(f1[global_row], f1_threshold, ONSET_INDEX - WINDOW)
            xmv_delay = first_persistent(xmv_level[global_row], xmv_pre_threshold, ONSET_INDEX)
            xmeas_delay = first_persistent(xmeas_level[global_row], xmeas_pre_threshold, ONSET_INDEX)
            f0_delays.append(f0_delay); f1_delays.append(f1_delay); xmv_delays.append(xmv_delay); xmeas_delays.append(xmeas_delay)
            run_rows.append({"fault_id": fault, "run_index": int(runs[global_row]), "run_id": int(selected.iloc[global_row]["run_id"]), "xmv_change_delay": xmv_delay, "xmeas_change_delay": xmeas_delay, "f0_alarm_delay": f0_delay, "f1_alarm_delay": f1_delay})

        pre_score = slice(399 - WINDOW, ONSET_INDEX - WINDOW)
        post_score = slice(ONSET_INDEX - WINDOW, 899 - WINDOW)
        rows.append({
            "fault_id": fault, "runs": int(idx.sum()),
            "xmv_level_auroc_early": xmv_auc, "xmv_level_auprc_early": xmv_auprc,
            "xmv_delta_auroc_early": xmv_delta_auc, "xmv_top3_shift_share": top3_share,
            "median_xmv_change_delay": float(np.nanmedian(xmv_delays)), "median_xmeas_change_delay": float(np.nanmedian(xmeas_delays)),
            "xmv_leads_xmeas_runs": float(np.mean(np.asarray(xmv_delays) < np.asarray(xmeas_delays))),
            "median_f0_alarm_delay": float(np.nanmedian(f0_delays)), "median_f1_alarm_delay": float(np.nanmedian(f1_delays)),
            "f1_earlier_alarm_runs": float(np.mean(np.nan_to_num(f1_delays, nan=np.inf) < np.nan_to_num(f0_delays, nan=np.inf))),
            "f0_prefault_score_over_threshold": float(np.mean(f0_fault[:, pre_score] / f0_threshold)),
            "f1_prefault_score_over_threshold": float(np.mean(f1_fault[:, pre_score] / f1_threshold)),
            "f0_early_fault_score_over_threshold": float(np.mean(f0_fault[:, post_score] / f0_threshold)),
            "f1_early_fault_score_over_threshold": float(np.mean(f1_fault[:, post_score] / f1_threshold)),
            "prefault_best_lag": pre_lag, "prefault_lag_corr": pre_corr,
            "postfault_best_lag": post_lag, "postfault_lag_corr": post_corr,
        })

        axis.plot(samples, np.median(xmv_level[idx], axis=0) / xmv_pre_threshold, label="XMV deviation / pre-99%")
        axis.plot(samples, np.median(xmeas_level[idx], axis=0) / xmeas_pre_threshold, label="XMEAS deviation / pre-99%")
        axis.plot(score_samples, np.median(f0_fault, axis=0) / f0_threshold, label="F0 score / threshold", alpha=.8)
        axis.plot(score_samples, np.median(f1_fault, axis=0) / f1_threshold, label="F1 score / threshold", alpha=.8)
        axis.axvline(600, color="black", linestyle="--", linewidth=1)
        axis.axhline(1, color="gray", linestyle=":", linewidth=1)
        axis.set_title(f"Fault {fault}"); axis.set_xlim(400, 900); axis.grid(alpha=.2)
    axes.flat[0].legend(fontsize=8)
    figure.supxlabel("sample (fault onset = 600)"); figure.supylabel("normalized magnitude")
    figure.tight_layout(); figure.savefig(figures / "reinartz_f1_mechanism_onset.png", dpi=160); plt.close(figure)

    pd.DataFrame(rows).to_csv(output / "reinartz_f1_mechanism_summary.csv", index=False)
    pd.DataFrame(feature_rows).to_csv(output / "reinartz_f1_xmv_feature_ranking.csv", index=False)
    pd.DataFrame(run_rows).to_csv(output / "reinartz_f1_mechanism_runs.csv", index=False)
    LOGGER.info("audit complete: %s", output / "reinartz_f1_mechanism_summary.csv")


if __name__ == "__main__":
    main()
