from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.config import load_config
from src.data.reinartz_f0_f1 import FAULT_ONSET, N_SAMPLES, build_cache, create_split, fit_scaler
from src.models.reinartz_forecaster import GRUForecaster

LOGGER = logging.getLogger(__name__)


class WindowDataset(Dataset):
    def __init__(self, features: np.ndarray, runs: np.ndarray, targets: np.ndarray, window: int, use_xmv: bool, mean: np.ndarray, std: np.ndarray) -> None:
        self.features, self.runs, self.targets, self.window = features, runs, targets, window
        self.input_dim = 52 if use_xmv else 41
        self.mean, self.std = mean, std

    def __len__(self) -> int:
        return len(self.runs) * len(self.targets)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, int, int]:
        run = int(self.runs[index // len(self.targets)])
        target = int(self.targets[index % len(self.targets)])
        sequence = np.array(self.features[run, target - self.window : target, : self.input_dim], copy=True)
        output = np.array(self.features[run, target, :41], copy=True)
        sequence = (sequence - self.mean[: self.input_dim]) / self.std[: self.input_dim]
        output = (output - self.mean[:41]) / self.std[:41]
        return torch.from_numpy(sequence), torch.from_numpy(output), run, target + 1


def binary_metrics(labels: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    order = np.argsort(scores, kind="stable")
    ranks = np.empty_like(order, dtype=np.float64); ranks[order] = np.arange(1, len(scores) + 1)
    positive = labels == 1; n_pos, n_neg = positive.sum(), (~positive).sum()
    auroc = (ranks[positive].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    descending = np.argsort(-scores, kind="stable"); sorted_labels = labels[descending]
    precision = np.cumsum(sorted_labels) / np.arange(1, len(labels) + 1)
    auprc = precision[sorted_labels == 1].mean()
    return float(auroc), float(auprc)


def evaluate_scores(model: nn.Module, loader: DataLoader, device: torch.device, phase: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    model.eval(); scores, mean_squared_errors, runs, samples = [], [], [], []
    total_batches = len(loader)
    progress_interval = max(1, total_batches // 10)
    phase_started = time.perf_counter()
    LOGGER.info("%s scoring started: batches=%d samples=%d", phase, total_batches, len(loader.dataset))
    with torch.no_grad():
        for batch_index, (x, y, run, sample) in enumerate(loader, start=1):
            prediction = model(x.to(device, non_blocking=True)); residual = prediction - y.to(device, non_blocking=True)
            scores.append(torch.mean(torch.abs(residual), dim=1).cpu().numpy())
            mean_squared_errors.append(torch.mean(residual**2, dim=1).cpu().numpy())
            runs.append(run.numpy()); samples.append(sample.numpy())
            if batch_index % progress_interval == 0 or batch_index == total_batches:
                elapsed = time.perf_counter() - phase_started
                eta = elapsed / batch_index * (total_batches - batch_index)
                LOGGER.info("%s scoring: %d/%d batches (%.0f%%) elapsed=%.1fs ETA=%.1fs", phase, batch_index, total_batches, 100 * batch_index / total_batches, elapsed, eta)
    return np.concatenate(scores), np.concatenate(mean_squared_errors), np.concatenate(runs), np.concatenate(samples)


def persistence_delays(scores: np.ndarray, runs: np.ndarray, samples: np.ndarray, threshold: float, consecutive: int) -> tuple[float, float, float]:
    delays, detected, prealarm = [], 0, 0
    for run in np.unique(runs):
        mask = runs == run; order = np.argsort(samples[mask]); s, p = scores[mask][order], samples[mask][order]
        exceed = s >= threshold
        alarm = np.convolve(exceed.astype(int), np.ones(consecutive, dtype=int), mode="valid") >= consecutive
        alarm_samples = p[consecutive - 1 :]
        prealarm += int(np.any(alarm & (alarm_samples < FAULT_ONSET)))
        valid = np.flatnonzero(alarm & (alarm_samples >= FAULT_ONSET))
        if len(valid):
            detected += 1; delays.append(int(p[valid[0] + consecutive - 1] - FAULT_ONSET))
    n_runs = len(np.unique(runs))
    return detected / n_runs, float(np.mean(delays)) if delays else float("nan"), prealarm / n_runs


def run_model(config: dict, split, features, mean, std, variant: str, epochs: int, model_seed: int, hidden_dim: int | None = None) -> tuple[dict, list[dict]]:
    torch.manual_seed(model_seed)
    use_xmv = variant == "F1"
    requested_device = str(config.get("device", "auto"))
    if requested_device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("device=cuda was requested, but CUDA is unavailable. Install a CUDA-enabled PyTorch build.")
    device = torch.device("cuda" if requested_device == "cuda" or (requested_device == "auto" and torch.cuda.is_available()) else "cpu")
    use_cuda = device.type == "cuda"
    train_runs = split.loc[split.split == "train", "run_index"].to_numpy()
    val_runs = split.loc[split.split == "validation", "run_index"].to_numpy()
    test_runs = split.loc[split.split == "test", "run_index"].to_numpy()
    window = int(config["window"]); batch = int(config["batch_size"])
    train_targets = np.arange(window, FAULT_ONSET - 1)
    val_targets = np.arange(window, FAULT_ONSET - 1)
    test_targets = np.arange(window, N_SAMPLES)
    train_ds = WindowDataset(features, train_runs, train_targets, window, use_xmv, mean, std)
    val_ds = WindowDataset(features, val_runs, val_targets, window, use_xmv, mean, std)
    test_ds = WindowDataset(features, test_runs, test_targets, window, use_xmv, mean, std)
    generator = torch.Generator().manual_seed(model_seed)
    train_loader = DataLoader(train_ds, batch_size=batch, shuffle=True, num_workers=int(config["num_workers"]), generator=generator, pin_memory=use_cuda)
    val_loader = DataLoader(val_ds, batch_size=batch * 4, shuffle=False, pin_memory=use_cuda)
    test_loader = DataLoader(test_ds, batch_size=batch * 4, shuffle=False, pin_memory=use_cuda)
    model_hidden_dim = hidden_dim if hidden_dim is not None else int(config["hidden_dim"])
    model = GRUForecaster(train_ds.input_dim, model_hidden_dim, int(config["layers"])).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"])); loss_fn = nn.MSELoss()
    parameter_count = sum(p.numel() for p in model.parameters())
    LOGGER.info("[%s] training setup: device=%s input_dim=%d parameters=%d", variant, device, train_ds.input_dim, parameter_count)
    if use_cuda:
        properties = torch.cuda.get_device_properties(device)
        LOGGER.info("[%s] GPU ACTIVE: %s | CUDA %s | VRAM %.1f GB", variant, properties.name, torch.version.cuda, properties.total_memory / 1024**3)
    LOGGER.info("[%s] data: train=%d windows/%d batches, validation=%d windows, test=%d windows", variant, len(train_ds), len(train_loader), len(val_ds), len(test_ds))
    started = time.perf_counter()
    for epoch in range(epochs):
        epoch_started = time.perf_counter()
        model.train(); total = 0.0
        total_batches = len(train_loader)
        progress_interval = max(1, total_batches // 10)
        LOGGER.info("[%s] epoch %d/%d started", variant, epoch + 1, epochs)
        for batch_index, (x, y, _, _) in enumerate(train_loader, start=1):
            optimizer.zero_grad(); prediction = model(x.to(device, non_blocking=True)); loss = loss_fn(prediction, y.to(device, non_blocking=True)); loss.backward(); optimizer.step(); total += loss.item() * len(x)
            if batch_index % progress_interval == 0 or batch_index == total_batches:
                elapsed = time.perf_counter() - epoch_started
                eta = elapsed / batch_index * (total_batches - batch_index)
                samples_seen = min(batch_index * batch, len(train_ds))
                LOGGER.info("[%s] epoch %d/%d: batch %d/%d (%.0f%%) mse=%.6f elapsed=%.1fs ETA=%.1fs", variant, epoch + 1, epochs, batch_index, total_batches, 100 * batch_index / total_batches, total / samples_seen, elapsed, eta)
        LOGGER.info("[%s] epoch %d/%d (%.0f%%): train_mse=%.6f epoch=%.1fs total=%.1fs", variant, epoch + 1, epochs, 100 * (epoch + 1) / epochs, total / len(train_ds), time.perf_counter() - epoch_started, time.perf_counter() - started)
    val_scores, _, _, _ = evaluate_scores(model, val_loader, device, f"[{variant}] validation")
    threshold = float(np.percentile(val_scores, float(config["threshold_percentile"])))
    LOGGER.info("[%s] anomaly threshold: percentile=%.2f value=%.6f (validation normal only)", variant, float(config["threshold_percentile"]), threshold)
    test_scores, test_mse, test_run_index, test_samples = evaluate_scores(model, test_loader, device, f"[{variant}] test")
    labels_cache = np.load(Path(config["paths"]["cache"]) / "metadata.npz")["labels"]
    binary = (labels_cache[test_run_index, test_samples - 1] != 0).astype(np.int8)
    auroc, auprc = binary_metrics(binary, test_scores)
    detected, delay, prealarm_rate = persistence_delays(test_scores, test_run_index, test_samples, threshold, int(config["alarm_consecutive"]))
    normal = binary == 0
    metrics = {"variant": variant, "seed": model_seed, "split_seed": config["seed"], "epochs": epochs, "input_dim": train_ds.input_dim, "hidden_dim": model_hidden_dim, "parameters": parameter_count, "mae_z": float(test_scores[normal].mean()), "rmse_z": float(np.sqrt(np.mean(test_mse[normal]))), "auroc": auroc, "auprc": auprc, "detected_run_ratio": detected, "detection_delay": delay, "prefault_sample_fpr": float((test_scores[normal] >= threshold).mean()), "prefault_run_alarm_rate": prealarm_rate, "threshold": threshold, "elapsed_seconds": time.perf_counter() - started}
    fault_rows = []
    fault_ids = split.set_index("run_index").fault_id.to_dict()
    for fault in range(1, 29):
        fault_run_indices = np.array([run for run in test_runs if fault_ids[run] == fault])
        mask = np.isin(test_run_index, fault_run_indices); fault_binary = binary[mask]; fault_scores = test_scores[mask]
        f_auroc, f_auprc = binary_metrics(fault_binary, fault_scores)
        f_detected, f_delay, f_prealarm = persistence_delays(fault_scores, test_run_index[mask], test_samples[mask], threshold, int(config["alarm_consecutive"]))
        fault_rows.append({"variant": variant, "seed": model_seed, "split_seed": config["seed"], "fault_id": fault, "auroc": f_auroc, "auprc": f_auprc, "detected_run_ratio": f_detected, "detection_delay": f_delay, "prefault_run_alarm_rate": f_prealarm})
    checkpoint_slug = variant.lower().replace("-", "_")
    checkpoint = Path(config["paths"]["checkpoints"]) / f"reinartz_{checkpoint_slug}_seed_{model_seed}.pt"; checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": config, "variant": variant, "mean": mean, "std": std}, checkpoint)
    LOGGER.info("[%s] complete: AUROC=%.4f AUPRC=%.4f delay=%.2f checkpoint=%s", variant, auroc, auprc, delay, checkpoint)
    return metrics, fault_rows


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", default="configs/reinartz_f0_f1.yaml"); parser.add_argument("--epochs", type=int); parser.add_argument("--suffix", default=""); parser.add_argument("--model-seed", type=int)
    args = parser.parse_args(); config = load_config(args.config); epochs = args.epochs or int(config["epochs"]); model_seed = args.model_seed or int(config["seed"])
    random.seed(model_seed); np.random.seed(model_seed); torch.manual_seed(model_seed); torch.use_deterministic_algorithms(True)
    log_dir = Path(config["paths"]["logs"]); log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(log_dir / f"seed_{model_seed}{args.suffix}.log", encoding="utf-8")])
    LOGGER.info("=== Reinartz TEP F0/F1 experiment started ===")
    LOGGER.info("config=%s split_seed=%s model_seed=%s epochs=%d window=%s horizon=%s batch=%s", args.config, config["seed"], model_seed, epochs, config["window"], config.get("horizon", 1), config["batch_size"])
    source, cache = Path(config["paths"]["source"]), Path(config["paths"]["cache"]); LOGGER.info("[stage 1/4] preparing cache from %s", source); LOGGER.info("cache=%s", build_cache(source, cache))
    LOGGER.info("[stage 2/4] creating leakage-safe train/validation/test split")
    split = create_split(cache / "metadata.npz", int(config["seed"]), int(config["validation_runs_per_fault"])); artifacts = Path(config["paths"]["artifacts"]); artifacts.mkdir(parents=True, exist_ok=True); split.to_csv(artifacts / "reinartz_split_manifest.csv", index=False)
    LOGGER.info("split runs=%s", split["split"].value_counts().to_dict())
    LOGGER.info("[stage 3/4] fitting scaler on training runs only")
    features = np.load(cache / "features.npy", mmap_mode="r"); train_runs = split.loc[split.split == "train", "run_index"].to_numpy(); mean, std = fit_scaler(features, train_runs)
    with (artifacts / "reinartz_scaler_parameters.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(["feature", "mean", "std"]); [writer.writerow([f"xmeas_{i+1}" if i < 41 else f"xmv_{i-40}", mean[i], std[i]]) for i in range(52)]
    results, faults = [], []
    LOGGER.info("[stage 4/4] training and evaluating F0 then F1")
    for variant in ("F0", "F1"):
        metric, fault = run_model(config, split, features, mean, std, variant, epochs, model_seed); results.append(metric); faults.extend(fault); LOGGER.info("result=%s", json.dumps(metric))
    suffix = args.suffix or (f"_seed_{model_seed}" if args.model_seed is not None else "")
    pd = __import__("pandas"); pd.DataFrame(results).to_csv(artifacts / f"reinartz_f0_f1_results{suffix}.csv", index=False); pd.DataFrame(faults).to_csv(artifacts / f"reinartz_fault_results{suffix}.csv", index=False)
    LOGGER.info("=== experiment finished: results saved under %s ===", artifacts)


if __name__ == "__main__":
    main()
