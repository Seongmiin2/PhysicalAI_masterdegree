"""Stage 1A: isolate training budget using normal-validation checkpoint selection."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import time
import traceback

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
import yaml
import run_architecture_gate_g2 as architectures

ROOT = Path(__file__).resolve().parents[1]
experiment = architectures.experiment
LOG = logging.getLogger('chum.training_budget')


class EarlyStop:
    def __init__(self, patience, min_delta, min_epochs):
        self.patience, self.min_delta, self.min_epochs = patience, min_delta, min_epochs
        self.best = self.reference = float('inf')
        self.bad_epochs = 0
        self.best_epoch = 0

    def update(self, loss, epoch):
        if not np.isfinite(loss):
            raise ValueError('Non-finite validation loss')
        improved = loss < self.best
        if improved:
            self.best, self.best_epoch = loss, epoch
        if loss < self.reference - self.min_delta:
            self.reference, self.bad_epochs = loss, 0
        else:
            self.bad_epochs += 1
        return improved, epoch >= self.min_epochs and self.bad_epochs >= self.patience


def validation_mse(model, loader, device):
    model.eval()
    total, count = 0.0, 0
    with torch.inference_mode():
        for x, y, _, _ in loader:
            residual = model(x.to(device, non_blocking=True)) - y.to(device, non_blocking=True)
            total += float(residual.square().sum())
            count += residual.numel()
    return total / count


def censored_delays(scores, runs, samples, threshold, consecutive):
    delays = []
    for run in np.unique(runs):
        mask = runs == run
        order = np.argsort(samples[mask])
        positions, values = samples[mask][order], scores[mask][order]
        alarms = np.convolve((values >= threshold).astype(int), np.ones(consecutive, dtype=int), mode='valid') >= consecutive
        alarm_times = positions[consecutive-1:]
        detected = alarm_times[alarms & (alarm_times >= experiment.FAULT_ONSET)]
        delays.append(float(detected[0] - experiment.FAULT_ONSET) if len(detected) else float(positions[-1] - experiment.FAULT_ONSET + 1))
    return float(np.mean(delays))


def run_task(cfg, architecture, variant, seed, split, features, mean, std, output, update_status):
    task = f'{architecture}_{variant}_seed{seed}'
    task_dir = output / task
    task_dir.mkdir(parents=True, exist_ok=True)
    architectures.ARCH = architecture
    width = int(cfg['hidden_dim'])
    if variant == 'F0-C':
        width = architectures.matched_width(architectures.count(52, width, int(cfg['layers'])), int(cfg['layers']))
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    device = torch.device('cuda')
    window, batch = int(cfg['window']), int(cfg['batch_size'])
    if window != 20:
        raise ValueError('Stage 1A fixes window=20; extended windows need a separate design')
    def dataset(group, targets):
        runs = split.loc[split.split == group, 'run_index'].to_numpy()
        return experiment.WindowDataset(features, runs, targets, window, variant == 'F1', mean, std)
    normal_targets = np.arange(window, experiment.FAULT_ONSET - 1)
    train_ds = dataset('train', normal_targets)
    validation_ds = dataset('validation', normal_targets)
    train_loader = DataLoader(train_ds, batch_size=batch, shuffle=True, generator=torch.Generator().manual_seed(seed), num_workers=0, pin_memory=True)
    val_loader = DataLoader(validation_ds, batch_size=batch*4, shuffle=False, num_workers=0, pin_memory=True)
    model = architectures.factory(train_ds.input_dim, width, int(cfg['layers'])).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(cfg['learning_rate']))
    stopping = EarlyStop(int(cfg['patience']), float(cfg['min_delta']), int(cfg['min_epochs']))
    history = []
    started = time.perf_counter()
    def save_checkpoint(name, epoch):
        torch.save({'state_dict': model.state_dict(), 'optimizer_state_dict': optimizer.state_dict(), 'config': cfg, 'architecture': architecture, 'variant': variant, 'seed': seed, 'epoch': epoch, 'mean': mean, 'std': std}, task_dir / name)
    LOG.info('%s START gpu=%s train_windows=%d normal_validation_windows=%d', task, torch.cuda.get_device_name(), len(train_ds), len(validation_ds))
    for epoch in range(1, int(cfg['epochs'])+1):
        update_status(task=task, stage='training', epoch=epoch, max_epochs=cfg['epochs'])
        model.train()
        total, count = 0.0, 0
        for index, (x, y, _, _) in enumerate(train_loader, 1):
            optimizer.zero_grad()
            residual = model(x.to(device, non_blocking=True)) - y.to(device, non_blocking=True)
            loss = residual.square().mean()
            if not torch.isfinite(loss):
                raise ValueError('Non-finite training loss')
            loss.backward()
            optimizer.step()
            total += float(loss.detach()) * len(x)
            count += len(x)
            if index % max(1, len(train_loader)//4) == 0 or index == len(train_loader):
                LOG.info('%s epoch=%d/%d batches=%d/%d train_mse=%.6f', task, epoch, cfg['epochs'], index, len(train_loader), total/count)
        val_loss = validation_mse(model, val_loader, device)
        improved, stop = stopping.update(val_loss, epoch)
        if improved:
            save_checkpoint('best.pt', epoch)
        if epoch == 10:
            save_checkpoint('epoch10.pt', epoch)
        history.append({'epoch':epoch, 'train_mse':total/count, 'validation_mse':val_loss, 'best_epoch':stopping.best_epoch, 'bad_epochs':stopping.bad_epochs, 'elapsed_seconds':time.perf_counter()-started})
        pd.DataFrame(history).to_csv(task_dir/'TRAINING_HISTORY.csv', index=False)
        LOG.info('%s epoch=%d validation_mse=%.6f best_epoch=%d patience=%d/%d', task, epoch, val_loss, stopping.best_epoch, stopping.bad_epochs, stopping.patience)
        if stop:
            LOG.info('%s EARLY STOP at epoch=%d', task, epoch)
            break
    checkpoint = torch.load(task_dir/'best.pt', map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['state_dict'])
    update_status(task=task, stage='evaluate_selected_checkpoint', epoch=epoch, best_epoch=stopping.best_epoch)
    val_scores, _, _, _ = experiment.evaluate_scores(model, val_loader, device, task+' calibration')
    threshold = float(np.percentile(val_scores, float(cfg['threshold_percentile'])))
    test_ds = dataset('test', np.arange(window, experiment.N_SAMPLES))
    test_loader = DataLoader(test_ds, batch_size=batch*4, shuffle=False, num_workers=0, pin_memory=True)
    scores, _, runs, samples = experiment.evaluate_scores(model, test_loader, device, task+' test')
    with np.load((ROOT / cfg['paths']['cache'])/'metadata.npz') as metadata:
        labels = (metadata['labels'][runs, samples-1] != 0).astype(np.int8)
    def metrics(mask):
        s, r, p, y = scores[mask], runs[mask], samples[mask], labels[mask]
        auroc, auprc = experiment.binary_metrics(y, s)
        detected, delay, prealarm = experiment.persistence_delays(s,r,p,threshold,int(cfg['alarm_consecutive']))
        return {'auroc':float(auroc),'auprc':float(auprc),'detected_run_ratio':float(detected),'missed_run_ratio':float(1-detected),'detection_delay_detected_only':float(delay),'censored_delay_mean':censored_delays(s,r,p,threshold,int(cfg['alarm_consecutive'])),'prefault_sample_fpr':float((s[y==0]>=threshold).mean()),'prefault_run_alarm_rate':float(prealarm)}
    result = {'architecture':architecture,'variant':variant,'seed':seed,'epochs_run':epoch,'best_epoch':stopping.best_epoch,'best_validation_mse':stopping.best,'parameters':sum(p.numel() for p in model.parameters()),'threshold':threshold,'elapsed_seconds':time.perf_counter()-started,**metrics(np.ones(len(scores),dtype=bool))}
    fault_rows=[]
    for fault, group in split.loc[split.split=='test'].groupby('fault_id'):
        fault_rows.append({'architecture':architecture,'variant':variant,'seed':seed,'fault_id':int(fault),**metrics(np.isin(runs,group.run_index.to_numpy()))})
    pd.DataFrame(fault_rows).to_csv(task_dir/'FAULT_RESULTS.csv',index=False)
    (task_dir/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    LOG.info('%s COMPLETE best_epoch=%d AUROC=%.6f AUPRC=%.6f',task,stopping.best_epoch,result['auroc'],result['auprc'])
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/chum_training_budget.yaml')
    args=parser.parse_args()
    path=ROOT/args.config
    cfg=yaml.safe_load(path.read_text(encoding='utf-8'))
    output=ROOT/cfg['paths']['output']
    output.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    state={'status':'RUNNING','pid':os.getpid(),'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'stage':'initializing','completed_tasks':0}
    def update_status(**changes):
        state.update(changes)
        state['updated_at']=time.strftime('%Y-%m-%dT%H:%M:%S%z')
        temporary=output/'LIVE_STATUS.tmp'
        temporary.write_text(json.dumps(state,indent=2),encoding='utf-8')
        temporary.replace(output/'LIVE_STATUS.json')
    status_path=output/'LIVE_STATUS.json'
    if status_path.exists():
        previous=json.loads(status_path.read_text(encoding='utf-8'))
        if previous['config_sha256']!=state['config_sha256']:
            raise ValueError('Use a new output directory for a changed configuration')
    update_status()
    try:
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA required for this experiment')
        split=pd.read_csv(ROOT/'outputs/final_gate_exp1/artifacts/reinartz_split_manifest.csv')
        scaler=pd.read_csv(ROOT/'outputs/final_gate_exp1/artifacts/reinartz_scaler_parameters.csv')
        mean,std=scaler['mean'].to_numpy(np.float32),scaler['std'].to_numpy(np.float32)
        features=np.load((ROOT / cfg['paths']['cache'])/'features.npy',mmap_mode='r')
        results=[]
        for architecture in cfg['architectures']:
            for seed in cfg['model_seeds']:
                for variant in cfg['variants']:
                    result_path=output/f'{architecture}_{variant}_seed{seed}'/'RESULT.json'
                    if result_path.exists():
                        result=json.loads(result_path.read_text(encoding='utf-8'))
                    else:
                        result=run_task(cfg,architecture,variant,int(seed),split,features,mean,std,output,update_status)
                    results.append(result)
                    pd.DataFrame(results).to_csv(output/'METRICS.csv',index=False)
                    update_status(completed_tasks=len(results))
        update_status(status='COMPLETE',stage='finished')
    except Exception:
        update_status(status='FAILED',error=traceback.format_exc())
        raise


if __name__=='__main__':
    main()
