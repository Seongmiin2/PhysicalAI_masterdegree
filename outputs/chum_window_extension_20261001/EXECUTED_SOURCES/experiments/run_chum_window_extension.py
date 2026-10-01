"""Stage 1B: equal-capacity window comparison on common target samples.

The old test split is a development benchmark, not an untouched holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import platform
import time
import traceback

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader
import yaml
from run_chum_training_budget import EarlyStop, validation_mse, censored_delays, experiment
from window_metrics import binary_metrics

ROOT = Path(__file__).resolve().parents[1]


class CausalTCN(nn.Module):
    def __init__(self, input_dim, width, layers):
        super().__init__()
        blocks = []
        for i in range(layers):
            dilation = 2 ** i
            blocks.extend([nn.ConstantPad1d((2 * dilation, 0), 0),
                           nn.Conv1d(input_dim if i == 0 else width, width, 3, dilation=dilation),
                           nn.GELU()])
        self.network = nn.Sequential(*blocks)
        self.output = nn.Linear(width, 41)
        self.receptive_field = 1 + 2 * (2 ** layers - 1)

    def forward(self, sequence):
        return self.output(self.network(sequence.transpose(1, 2))[:, :, -1])


class WindowTransformer(nn.Module):
    def __init__(self, input_dim, width, layers, max_window):
        super().__init__()
        self.projection = nn.Linear(input_dim, width)
        self.position = nn.Parameter(torch.zeros(1, max_window, width))
        layer = nn.TransformerEncoderLayer(width, 4, width * 2, dropout=0.0,
                    activation='gelu', batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(width)
        self.output = nn.Linear(width, 41)

    def forward(self, sequence):
        if sequence.shape[1] > self.position.shape[1]:
            raise ValueError('Sequence exceeds fixed positional capacity')
        # Align positions by lag, so the most recent sample always has the same position.
        hidden = self.encoder(self.projection(sequence) + self.position[:, -sequence.shape[1]:])
        return self.output(self.norm(hidden[:, -1]))


def build_model(cfg, architecture, variant):
    def factory(inputs, width):
        if architecture == 'tcn':
            return CausalTCN(inputs, width, int(cfg['tcn_layers']))
        if architecture == 'transformer':
            return WindowTransformer(inputs, width, int(cfg['transformer_layers']), int(cfg['max_window']))
        raise ValueError(f'Unknown architecture: {architecture}')
    if variant not in ('F0', 'F1', 'F0-C'):
        raise ValueError(f'Unknown variant: {variant}')
    width = int(cfg['hidden_dim'])
    if variant == 'F0-C':
        # Parameter counting must not perturb the seeded training initialization.
        with torch.random.fork_rng(devices=[]):
            target = sum(p.numel() for p in factory(52, width).parameters())
            # Keep four attention heads in every Transformer capacity control.
            widths = range(8, 129, 4 if architecture == 'transformer' else 1)
            width = min(widths, key=lambda n: abs(sum(p.numel() for p in factory(41, n).parameters()) - target))
    return factory(52 if variant == 'F1' else 41, width)


def target_indices(cfg, group):
    # Equal training examples, calibration examples, and evaluation labels across windows.
    stop = experiment.N_SAMPLES if group == 'test' else experiment.FAULT_ONSET - 1
    return np.arange(int(cfg['max_window']), stop)


def validate_config(cfg):
    if not cfg['windows'] or min(cfg['windows']) < 1 or max(cfg['windows']) > cfg['max_window']:
        raise ValueError('All windows must fit max_window')
    if cfg['max_window'] >= experiment.FAULT_ONSET - 1:
        raise ValueError('Common normal target range is empty')
    if 1 + 2 * (2 ** int(cfg['tcn_layers']) - 1) < cfg['max_window']:
        raise ValueError('TCN receptive field must cover max_window')
    if cfg['hidden_dim'] % 4:
        raise ValueError('Transformer hidden width must be divisible by four')
    if cfg['epochs'] < 1 or cfg['batch_size'] < 1:
        raise ValueError('Epoch and batch budgets must be positive')


def run_task(cfg, architecture, variant, seed, window, split, features, mean, std, output, update, fingerprint):
    task = f'{architecture}_{variant}_seed{seed}_window{window}'
    task_dir = output / task
    task_dir.mkdir(parents=True, exist_ok=True)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    device = torch.device(cfg['device'])
    def dataset(group):
        runs = split.loc[split.split == group, 'run_index'].to_numpy()
        return experiment.WindowDataset(features, runs, target_indices(cfg, group), window, variant == 'F1', mean, std)
    def loader(group, shuffle=False):
        return DataLoader(dataset(group), batch_size=int(cfg['batch_size']), shuffle=shuffle,
                          generator=torch.Generator().manual_seed(seed), num_workers=0,
                          pin_memory=device.type == 'cuda')
    train_loader, val_loader = loader('train', True), loader('validation')
    model = build_model(cfg, architecture, variant).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(cfg['learning_rate']))
    stopping = EarlyStop(int(cfg['patience']), float(cfg['min_delta']), int(cfg['min_epochs']))
    history, started = [], time.perf_counter()
    for epoch in range(1, int(cfg['epochs']) + 1):
        update(task=task, stage='training', epoch=epoch)
        model.train()
        total, count = 0.0, 0
        for x, y, _, _ in train_loader:
            optimizer.zero_grad()
            loss = (model(x.to(device)) - y.to(device)).square().mean()
            if not torch.isfinite(loss):
                raise ValueError('Non-finite training loss')
            loss.backward()
            optimizer.step()
            total += float(loss.detach()) * len(x)
            count += len(x)
        val_loss = validation_mse(model, val_loader, device)
        improved, stop = stopping.update(val_loss, epoch)
        if improved:
            torch.save({'state_dict': model.state_dict(), 'config': cfg, 'architecture': architecture,
                        'variant': variant, 'seed': seed, 'window': window, 'epoch': epoch,
                        'mean': mean, 'std': std}, task_dir / 'best.pt')
        history.append({'epoch': epoch, 'train_mse': total/count, 'validation_mse': val_loss,
                        'best_epoch': stopping.best_epoch, 'elapsed_seconds': time.perf_counter()-started})
        pd.DataFrame(history).to_csv(task_dir / 'TRAINING_HISTORY.csv', index=False)
        logging.info('%s epoch=%d validation_mse=%.6f', task, epoch, val_loss)
        if stop:
            break
    model.load_state_dict(torch.load(task_dir/'best.pt', map_location=device, weights_only=False)['state_dict'])
    update(task=task, stage='calibration', best_epoch=stopping.best_epoch)
    val_scores, _, _, _ = experiment.evaluate_scores(model, val_loader, device, task+' calibration')
    threshold = float(np.percentile(val_scores, cfg['threshold_percentile']))
    result = {'architecture': architecture, 'variant': variant, 'seed': seed, 'window': window,
              'parameters': sum(p.numel() for p in model.parameters()), 'epochs_run': epoch,
              'best_epoch': stopping.best_epoch, 'best_validation_mse': stopping.best,
              'threshold': threshold, 'evaluation_role': 'development_benchmark',
              'common_first_sample': int(cfg['max_window'])+1, 'test_evaluated': False,
              'run_fingerprint': fingerprint}
    if cfg.get('evaluate_test', False):
        update(task=task, stage='evaluate_selected_checkpoint')
        scores, _, runs, samples = experiment.evaluate_scores(model, loader('test'), device, task+' development test')
        with np.load(Path(cfg['paths']['cache'])/'metadata.npz') as metadata:
            labels = (metadata['labels'][runs, samples-1] != 0).astype(np.int8)
        auroc, auprc = binary_metrics(labels, scores)
        detected, delay, prealarm = experiment.persistence_delays(scores, runs, samples, threshold, cfg['alarm_consecutive'])
        result.update(test_evaluated=True, auroc=auroc, auprc=auprc, detected_run_ratio=detected,
                      missed_run_ratio=1-detected, detection_delay_detected_only=delay,
                      censored_delay_mean=censored_delays(scores, runs, samples, threshold, cfg['alarm_consecutive']),
                      prefault_sample_fpr=float((scores[labels == 0] >= threshold).mean()),
                      prefault_run_alarm_rate=prealarm)
    result['elapsed_seconds'] = time.perf_counter()-started
    temporary_result = task_dir/'RESULT.tmp'
    temporary_result.write_text(json.dumps(result, indent=2), encoding='utf-8')
    temporary_result.replace(task_dir/'RESULT.json')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/chum_window_extension.yaml')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--max-tasks', type=int, help='Stop after this many newly completed tasks; rerun to continue')
    parser.add_argument('--smoke', action='store_true', help='Synthetic CPU execution; never a research result')
    args = parser.parse_args()
    if args.max_tasks is not None and args.max_tasks < 1:
        parser.error('--max-tasks must be positive')
    cfg = yaml.safe_load((ROOT/args.config).read_text(encoding='utf-8'))
    validate_config(cfg)
    if args.dry_run:
        rows = []
        for architecture in cfg['architectures']:
            for variant in cfg['variants']:
                model = build_model(cfg, architecture, variant)
                rows.append({'architecture': architecture, 'variant': variant,
                             'parameters': sum(p.numel() for p in model.parameters())})
        print(json.dumps({'tasks': len(cfg['architectures'])*len(cfg['variants'])*len(cfg['windows'])*len(cfg['model_seeds']),
                          'common_first_sample': cfg['max_window']+1,
                          'normal_targets_per_run': len(target_indices(cfg, 'validation')),
                          'tcn_receptive_field': 1+2*(2**cfg['tcn_layers']-1), 'models': rows}, indent=2))
        return
    if args.smoke:
        torch.set_num_threads(1)
        for architecture in cfg['architectures']:
            for window in cfg['windows']:
                model = build_model(cfg, architecture, 'F1')
                loss = model(torch.randn(2, window, 52)).square().mean()
                loss.backward()
                assert torch.isfinite(loss)
        print(json.dumps({'status': 'PASS', 'kind': 'synthetic_forward_backward', 'research_result': False}))
        return
    if cfg['device'] == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA required by configuration')
    output = ROOT/cfg['paths']['output']
    output.mkdir(parents=True, exist_ok=True)
    source_paths = (Path(__file__).resolve(), ROOT/'experiments/run_chum_training_budget.py',
                    ROOT/'experiments/run_architecture_gate_g2.py', ROOT/'experiments/window_metrics.py',
                    Path(experiment.__file__).resolve(), ROOT.parent/'PhysicalAI_mini/src/data/reinartz_f0_f1.py',
                    ROOT/'outputs/final_gate_exp1/artifacts/reinartz_split_manifest.csv',
                    ROOT/'outputs/final_gate_exp1/artifacts/reinartz_scaler_parameters.csv')
    source_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
    cache = Path(cfg['paths']['cache'])
    features = np.load(cache/'features.npy', mmap_mode='r')
    stat = (cache/'features.npy').stat()
    cache_identity = {'path': str(cache.resolve()), 'shape': list(features.shape), 'dtype': str(features.dtype),
                      'size_bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
                      'metadata_sha256': hashlib.sha256((cache/'metadata.npz').read_bytes()).hexdigest(),
                      'feature_content_hashed': False}
    runtime_versions = {'python': platform.python_version(), 'torch': str(torch.__version__),
                        'numpy': np.__version__, 'pandas': pd.__version__, 'cuda': torch.version.cuda,
                        'device': str(cfg['device']),
                        'device_name': torch.cuda.get_device_name() if cfg['device'] == 'cuda' else platform.processor()}
    fingerprint = hashlib.sha256(json.dumps({'config': cfg, 'sources': source_hashes,
                                            'cache': cache_identity, 'runtime': runtime_versions}, sort_keys=True).encode()).hexdigest()
    status_path = output/'LIVE_STATUS.json'
    if status_path.exists() and json.loads(status_path.read_text(encoding='utf-8'))['config_sha256'] != fingerprint:
        raise ValueError('Changed configuration requires a new output directory')
    state = {'status': 'RUNNING', 'pid': os.getpid(), 'config_sha256': fingerprint, 'source_sha256': source_hashes, 'cache_identity': cache_identity, 'runtime_versions': runtime_versions, 'completed_tasks': 0}
    def update(**changes):
        state.update(changes, updated_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
        temporary = output/'LIVE_STATUS.tmp'
        temporary.write_text(json.dumps(state, indent=2), encoding='utf-8')
        temporary.replace(status_path)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    update(stage='initializing')
    try:
        split = pd.read_csv(ROOT/'outputs/final_gate_exp1/artifacts/reinartz_split_manifest.csv')
        scaler = pd.read_csv(ROOT/'outputs/final_gate_exp1/artifacts/reinartz_scaler_parameters.csv')
        mean, std = scaler['mean'].to_numpy(np.float32), scaler['std'].to_numpy(np.float32)
        results = []
        newly_completed = 0
        for architecture in cfg['architectures']:
            for seed in cfg['model_seeds']:
                for variant in cfg['variants']:
                    for window in cfg['windows']:
                        result_path = output/f'{architecture}_{variant}_seed{seed}_window{window}'/'RESULT.json'
                        if result_path.exists():
                            result = json.loads(result_path.read_text(encoding='utf-8'))
                            expected = {'architecture': architecture, 'variant': variant, 'seed': seed,
                                        'window': window, 'run_fingerprint': fingerprint}
                            if any(result.get(key) != value for key, value in expected.items()):
                                raise ValueError(f'Completed result identity mismatch: {result_path}')
                        else:
                            if args.max_tasks is not None and newly_completed >= args.max_tasks:
                                update(status='PARTIAL', stage='task_budget_reached')
                                return
                            result = run_task(cfg, architecture, variant, seed, window, split, features, mean, std, output, update, fingerprint)
                            newly_completed += 1
                        results.append(result)
                        pd.DataFrame(results).to_csv(output/'METRICS.csv', index=False)
                        update(completed_tasks=len(results))
        update(status='COMPLETE', stage='finished')
    except Exception:
        update(status='FAILED', error=traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
