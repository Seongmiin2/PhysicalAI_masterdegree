from pathlib import Path
import json
import tempfile
import shutil
import numpy as np
import pandas as pd
from scipy.stats import t
import analyze_architecture_chum_sensitivity as sensitivity
import analyze_chum_multiplicity as multiplicity

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'outputs/closeout_validation'
output.mkdir(parents=True, exist_ok=True)
summary = multiplicity.historical_csv('outputs/architecture_chum_g3/G3_CELL_SUMMARY.csv')
runs = multiplicity.historical_csv('outputs/architecture_chum_g3/G3_RUN_RESULTS.csv')
bh = multiplicity.permutation_results(runs, summary, repeats=200000, random_seed=20260825)
expected = pd.read_csv(ROOT / 'outputs/chum_multiplicity/BH_FDR_RESULTS.csv')
pd.testing.assert_frame_equal(bh.reset_index(drop=True), expected, check_dtype=False, atol=1e-12, rtol=1e-10)
bh.to_csv(output / 'RECOMPUTED_BH_FDR_RESULTS.csv', index=False)
print('BH table matches retained results', flush=True)
with tempfile.TemporaryDirectory(prefix='chum-sensitivity-') as directory:
    archive = Path(directory)
    relative_dir = Path('outputs/chum_primary_sensitivity')
    inputs = ['configs/architecture_chum_sensitivity.yaml'] + [str(relative_dir / name) for name in ['SENSITIVITY_RUN_MANIFEST.json', 'SENSITIVITY_FAULT_RESULTS.csv', 'SENSITIVITY_RUN_RESULTS.csv']]
    for relative in inputs:
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    previous = sensitivity.ROOT
    try:
        sensitivity.ROOT = archive
        sensitivity.main()
    finally:
        sensitivity.ROOT = previous
    decision = json.loads((archive / relative_dir / 'SENSITIVITY_DECISION.json').read_text())
    expected_decision = json.loads((ROOT / relative_dir / 'SENSITIVITY_DECISION.json').read_text())
    if decision != expected_decision:
        raise AssertionError('Sensitivity decision mismatch')
    for source in (archive / relative_dir).glob('*.csv'):
        if 'SUMMARY' in source.name or 'CI' in source.name:
            shutil.copy2(source, output / source.name)
    shutil.copy2(archive / relative_dir / 'SENSITIVITY_DECISION.json', output / 'SENSITIVITY_DECISION.json')
metrics = multiplicity.historical_csv('outputs/hai_external_validation_v2/HAI_EXTERNAL_METRICS.csv')
wide = metrics.loc[metrics.label == 'attack'].pivot(index='seed', columns='variant', values=['auroc', 'auprc', 'etaf1'])
intervals = []
for metric in ['auroc', 'auprc', 'etaf1']:
    values = wide[(metric, 'F1')] - wide[(metric, 'F0')]
    margin = t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
    intervals.append({'metric': metric, 'mean': float(values.mean()), 'ci_low': float(values.mean() - margin), 'ci_high': float(values.mean() + margin), 'seeds': len(values)})
pd.DataFrame(intervals).to_csv(output / 'RECOMPUTED_HAI_SEED_INTERVALS.csv', index=False)
report = {'bh_matches_retained_table': True, 'permutation_repeats': 200000, 'sensitivity_decision_matches': True, 'sensitivity_bootstrap_repeats': 2000, 'hai_intervals': intervals}
(output / 'ROBUSTNESS_VALIDATION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))

