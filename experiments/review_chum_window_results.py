"""Review completed stage 1B artifacts without retraining or changing results."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs/chum_window_extension_20261001'


def main():
    sources = {}
    checks = []

    def read(path):
        raw = path.read_bytes()
        sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(raw).hexdigest()
        return raw.decode('utf-8-sig')

    def check(condition, label):
        if not condition:
            raise ValueError(label)
        checks.append(label)

    rows = list(csv.DictReader(read(OUTPUT / 'METRICS.csv').splitlines()))
    expected = set(itertools.product(['tcn', 'transformer'], ['F0', 'F1', 'F0-C'], [47], [20, 60, 120]))
    keys = [(r['architecture'], r['variant'], int(r['seed']), int(r['window'])) for r in rows]
    check(len(rows) == 18 and set(keys) == expected and len(set(keys)) == 18, 'complete_unique_18_task_grid')
    snapshot = json.loads(read(OUTPUT / 'EXECUTED_SOURCES/MANIFEST.json'))
    completion = json.loads(read(OUTPUT / 'COMPLETION_STATUS.json'))
    check(completion['status'] == 'COMPLETE' and completion['completed_tasks'] == 18
          and completion['config_sha256'] == snapshot['run_fingerprint'], 'frozen_completion_record')
    read(OUTPUT / 'EXECUTED_SOURCES/executed_config.yaml')
    for item in snapshot['sources']:
        path = ROOT / item['archived_path'].replace('\\', '/')
        read(path)
        check(sources[path.relative_to(ROOT).as_posix()] == item['sha256'], 'executed_source_hash:' + path.name)
    results = {}
    for row, key in zip(rows, keys):
        arch, variant, seed, window = key
        task = OUTPUT / f'{arch}_{variant}_seed{seed}_window{window}'
        result = json.loads(read(task / 'RESULT.json'))
        check(set(result) == set(row), 'matching_result_schema:' + task.name)
        for field, value in result.items():
            observed = row[field]
            if isinstance(value, bool):
                same = observed.lower() == str(value).lower()
            elif isinstance(value, (int, float)):
                same = math.isfinite(value) and math.isclose(float(observed), value, rel_tol=1e-12, abs_tol=1e-12)
            else:
                same = observed == value
            if not same:
                raise ValueError(f'CSV/JSON mismatch: {task.name}/{field}')
        check(True, 'csv_matches_result:' + task.name)
        check(result['test_evaluated'] and result['evaluation_role'] == 'development_benchmark'
              and result['common_first_sample'] == 121
              and result['run_fingerprint'] == snapshot['run_fingerprint'], 'shared_evaluation_contract:' + task.name)
        for field in ['auroc', 'auprc', 'detected_run_ratio', 'missed_run_ratio', 'prefault_sample_fpr', 'prefault_run_alarm_rate']:
            if not 0 <= result[field] <= 1:
                raise ValueError(f'Invalid rate: {task.name}/{field}')
        check(math.isclose(result['detected_run_ratio'] + result['missed_run_ratio'], 1.0), 'detection_complement:' + task.name)
        history = list(csv.DictReader(read(task / 'TRAINING_HISTORY.csv').splitlines()))
        check([int(r['epoch']) for r in history] == list(range(1, result['epochs_run'] + 1)), 'complete_epoch_history:' + task.name)
        best = min(history, key=lambda r: float(r['validation_mse']))
        check(int(best['epoch']) == result['best_epoch'] and math.isclose(float(best['validation_mse']), result['best_validation_mse'], rel_tol=1e-12), 'validation_selected_checkpoint:' + task.name)
        results[key] = result
    for arch, variant in itertools.product(['tcn', 'transformer'], ['F0', 'F1', 'F0-C']):
        check(len({results[arch, variant, 47, w]['parameters'] for w in [20, 60, 120]}) == 1, f'constant_capacity_across_windows:{arch}/{variant}')
    f1_rows = []
    for arch, window in itertools.product(['tcn', 'transformer'], [20, 60, 120]):
        r = results[arch, 'F1', 47, window]
        summary = {name: r[name] for name in ['architecture', 'window', 'auroc', 'auprc', 'detected_run_ratio', 'prefault_sample_fpr', 'censored_delay_mean']}
        summary['delta_auroc_vs_window20'] = r['auroc'] - results[arch, 'F1', 47, 20]['auroc']
        summary['delta_auroc_vs_F0'] = r['auroc'] - results[arch, 'F0', 47, window]['auroc']
        summary['delta_auroc_vs_F0-C'] = r['auroc'] - results[arch, 'F0-C', 47, window]['auroc']
        f1_rows.append(summary)
    excluded = {'variant', 'elapsed_seconds'}
    transformer_duplicates = all(
        {k: v for k, v in results['transformer', 'F0', 47, w].items() if k not in excluded}
        == {k: v for k, v in results['transformer', 'F0-C', 47, w].items() if k not in excluded}
        for w in [20, 60, 120]
    )
    review = {
        'review_date': '2026-10-02', 'status': 'PASS', 'scope': 'Saved artifact consistency and descriptive comparisons; no retraining, raw score recomputation, or new statistical inference.',
        'task_count': len(rows), 'independent_training_seeds': [47], 'evaluation_role': 'development_benchmark',
        'experiment_completed_at': completion['updated_at'],
        'metric_definitions': {
            'auprc': 'Tie-aware non-interpolated average precision (AP), not classification accuracy.',
            'censored_delay_mean': 'Mean delay in samples with 1401 assigned to each undetected run; not a survival-analysis censoring estimator.',
            'prefault_sample_fpr': 'Point-level threshold exceedance fraction; distinct from the three-consecutive-sample run alarm rate.',
        },
        'run_fingerprint': snapshot['run_fingerprint'], 'checks_passed': len(checks), 'checks': checks,
        'source_sha256': sources, 'F1_comparisons': f1_rows,
        'transformer_F0_and_F0C_identical_except_variant_and_elapsed_time': transformer_duplicates,
        'best_checkpoint_at_epoch_limit_count': sum(r['best_epoch'] == 50 for r in results.values()),
        'interpretation': 'Longer windows do not yield a monotonic F1 AUROC improvement. F1 exceeds F0 and F0-C descriptively at all six architecture/window settings. Do not choose a final window by these observed development-test scores.',
        'limitations': [
            'One training seed and reused development test; no untouched holdout or seed uncertainty interval.',
            'Transformer F0-C and F0 collapse to the same model, so they are not independent capacity controls.',
            'Stage 1A and 1B also differ in architecture, sample range, batch size and metric implementation; their differences are not a window-only causal effect.',
            'Per-run score arrays were not saved by this runner; metric recomputation and run-cluster uncertainty were not performed here.',
            'Sample FPR and three-consecutive-sample run alarm rate have different denominators; neither is event-level detection accuracy.',
        ],
    }
    (OUTPUT / 'REVIEW_20261002.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    with (OUTPUT / 'F1_WINDOW_COMPARISON.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(f1_rows[0]))
        writer.writeheader()
        writer.writerows(f1_rows)
    print(json.dumps({'tasks': len(rows), 'checks_passed': len(checks), 'transformer_duplicate_control': transformer_duplicates, 'F1_comparisons': f1_rows}, indent=2))


if __name__ == '__main__':
    main()