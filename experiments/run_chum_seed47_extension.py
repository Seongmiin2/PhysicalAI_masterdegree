from pathlib import Path
import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs/chum_seed47_20260921'

def main():
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    os.environ['PYTHONUNBUFFERED'] = '1'
    state = {'pid': os.getpid(), 'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'RUNNING', 'stage': 'training', 'python': sys.executable}
    def save():
        (OUTPUT / 'LIVE_STATUS.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
    save()
    try:
        subprocess.run([sys.executable, '-u', 'experiments/run_architecture_gate_g2.py', '--config', 'configs/chum_seed47_training.yaml', '--seeds', '47', '--architectures', 'tcn', 'transformer'], cwd=ROOT, check=True)
        state['stage'] = 'channel_experiment'
        save()
        subprocess.run([sys.executable, '-u', 'experiments/run_architecture_chum_sensitivity.py', '--config', 'configs/chum_seed47_channel.yaml'], cwd=ROOT, check=True)
        import pandas as pd
        table = pd.read_csv(OUTPUT / 'channel/SENSITIVITY_FAULT_RESULTS.csv')
        keys = ['architecture', 'seed', 'fault_id']
        original = table.loc[table['mode'] == 'original', keys + ['auroc','auprc','pre_fpr']].rename(columns={name:'original_'+name for name in ['auroc','auprc','pre_fpr']})
        result = table.loc[table['mode'] == 'loo_sample'].merge(original, on=keys, validate='many_to_one')
        for metric in ['auroc','auprc']:
            result['delta_'+metric] = result['original_'+metric] - result[metric]
        result['delta_pre_fpr'] = result.pre_fpr - result.original_pre_fpr
        result.to_csv(OUTPUT / 'NEW_SEED_CHANNEL_EFFECTS.csv', index=False)
        state.update(status='COMPLETE', stage='finished', finished_at=datetime.now(timezone.utc).isoformat())
        save()
    except Exception:
        state.update(status='FAILED', error=traceback.format_exc(), finished_at=datetime.now(timezone.utc).isoformat())
        save()
        raise

if __name__ == '__main__':
    main()
