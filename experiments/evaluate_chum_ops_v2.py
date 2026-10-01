"""Freeze validation-only model selection before extracting and evaluating V2 test.

Both evaluation models receive the same raw evidence records. Their immutable
router metadata determines preprocessing. V1 consumed test is development only.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from providers.finetuned import ACTIONS, FineTunedProvider, record_text
from experiments.finetune_chum_ops_v2 import classification_metrics


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def rows(path):
    result = [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    if not result or any(row.get('label') not in ACTIONS for row in result):
        raise ValueError('Evaluation requires nonempty rows with valid action labels')
    return result


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def resolve(path):
    path = Path(path)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def adapter_files(path):
    return {str((Path(path) / name).resolve()): sha(Path(path) / name) for name in
            ('adapter_model.safetensors', 'adapter_config.json', 'router_config.json')}


def select_candidate(reports):
    candidates = []
    for path in reports:
        report = read(path)
        if 'heldout_test' in report or report.get('config', {}).get('test'):
            raise ValueError('Candidate report already contains test evaluation')
        validation = report['selected_validation']
        macro, loss = float(validation['macro_f1']), float(validation['loss'])
        if not math.isfinite(macro) or not math.isfinite(loss) or not 0 <= macro <= 1 or loss < 0:
            raise ValueError('Invalid validation metrics')
        adapter = resolve(report['config']['output'])
        if sha(adapter / 'adapter_model.safetensors') != report['adapter_sha256']:
            raise ValueError('Candidate adapter differs from its training report')
        candidates.append({'report': str(Path(path).resolve()), 'report_sha256': sha(path),
                           'adapter': str(adapter), 'files': adapter_files(adapter),
                           'validation_macro_f1': macro, 'validation_loss': loss,
                           'selected_epoch': report.get('selected_epoch')})
    if not candidates:
        raise ValueError('No candidate reports')
    chosen = sorted(candidates, key=lambda c: (-c['validation_macro_f1'], c['validation_loss'], c['report']))[0]
    return candidates, chosen


def freeze_selection(directory, reports, v1_adapter):
    directory = Path(directory)
    if any((directory / name).exists() for name in ('test_raw.jsonl', 'test_normalized.jsonl', 'HOLDOUT_EXTRACTION.json')):
        raise ValueError('Selection must be frozen before test extraction')
    if (directory / 'MODEL_SELECTION.json').exists():
        raise ValueError('Model selection is immutable')
    candidates, chosen = select_candidate(reports)
    data_files = {str((directory / name).resolve()): sha(directory / name) for name in
                  ('train_raw.jsonl', 'validation_raw.jsonl', 'train_normalized.jsonl', 'validation_normalized.jsonl',
                   'DATASET_MANIFEST.json', 'HOLDOUT_ASSIGNMENT.json', 'HOLDOUT_INCLUSION_POLICY.json')}
    code = {str(path.resolve()): sha(path) for path in
            (Path(__file__), ROOT / 'providers/finetuned.py', ROOT / 'providers/ops_features.py',
             ROOT / 'experiments/build_chum_ops_v2_dataset.py', ROOT / 'experiments/finetune_chum_ops_v2.py')}
    result = {'created_at': datetime.now(timezone.utc).isoformat(),
              'selection_rule': 'Highest selected_validation full-five-action macro_f1, then lower loss, then report path.',
              'candidates': candidates, 'selected': chosen, 'v1_adapter': str(Path(v1_adapter).resolve()),
              'v1_files': adapter_files(v1_adapter), 'data_files': data_files, 'code_files': code,
              'test_opened_for_selection': False, 'production_gate': False}
    write_new(directory / 'MODEL_SELECTION.json', result)
    return result


def verify_selection(path):
    frozen = read(path)
    checks = dict(frozen['data_files']) | frozen['code_files'] | frozen['v1_files']
    for candidate in frozen['candidates']:
        checks[candidate['report']] = candidate['report_sha256']
        checks.update(candidate['files'])
    for file, expected in checks.items():
        if sha(file) != expected:
            raise ValueError('Frozen selection artifact changed: ' + file)
    # Recompute the stated validation-only winner, rather than trusting a changed pointer.
    winner = sorted(frozen['candidates'], key=lambda c: (-c['validation_macro_f1'], c['validation_loss'], c['report']))[0]
    if frozen['selected'] != winner:
        raise ValueError('Frozen selected model is inconsistent')
    return frozen


def metrics(predictions):
    result = classification_metrics(predictions)
    supported = [entry['f1'] for entry in result['classwise'].values() if entry['support']]
    result['macro_f1_full_five_actions'] = result.pop('macro_f1')
    result['macro_f1_supported_classes'] = sum(supported) / len(supported)
    result['independent_groups'] = len({p['group_id'] for p in predictions})
    for key, output in (('artifact_type', 'by_artifact_type'), ('group_id', 'by_group')):
        result[output] = {}
        for value in sorted({p[key] for p in predictions}):
            subset = classification_metrics([p for p in predictions if p[key] == value])
            subset.pop('predictions')
            supported_f1 = [c['f1'] for c in subset['classwise'].values() if c['support']]
            subset['macro_f1_full_five_actions'] = subset.pop('macro_f1')
            subset['macro_f1_supported_classes'] = sum(supported_f1) / len(supported_f1)
            result[output][value] = subset
    return result


def evidence_object(row):
    try:
        parsed = json.loads(record_text(row))
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def rule_action(row):
    evidence = evidence_object(row)
    status = str(evidence.get('status', '')).upper()
    kind = evidence.get('artifact_type', '')
    if status in ('FAILED', 'ERROR') or kind == 'agent_failure_event':
        return 'INVESTIGATE_FAILURE'
    if status == 'PARTIAL':
        return 'RESUME_INCOMPLETE'
    if status in ('COMPLETE', 'COMPLETED') or kind.startswith('published_final'):
        return 'REVIEW_COMPLETED'
    if status == 'RUNNING' or kind == 'historical_training_epoch':
        return 'MONITOR_RUNNING'
    return 'REQUIRE_HUMAN_REVIEW'


def prediction(row, action):
    return {'record_id': row.get('record_id'), 'group_id': row['provenance']['group_id'],
            'artifact_type': evidence_object(row).get('artifact_type', 'unknown'),
            'expected': row['label'], 'predicted': action}


def baseline_reports(evaluation_rows, train_rows):
    counts = Counter(row['label'] for row in train_rows)
    majority = sorted(counts, key=lambda action: (-counts[action], action))[0]
    started = time.perf_counter()
    rule_predictions = [prediction(row, rule_action(row)) for row in evaluation_rows]
    rule_seconds = time.perf_counter() - started
    return {'majority_train': {'label': majority, 'training_counts': dict(counts),
                               **metrics([prediction(row, majority) for row in evaluation_rows])},
            'observed_state_rule': {'latency_seconds': rule_seconds,
                'limitation': 'Reproduces rule-generated labels on structured records; not independent human decision ground truth.',
                **metrics(rule_predictions)}}


def evaluate_models(datasets, adapters, provider_factory=FineTunedProvider):
    results = {name: {} for name in datasets}
    for version, adapter in adapters.items():
        provider = provider_factory(adapter_path=adapter, device='cpu')
        for dataset_name, dataset_rows in datasets.items():
            predictions = []
            for row in dataset_rows:
                routed = provider.route(row)
                predictions.append(prediction(row, routed['next_action']) | {
                    'probabilities': routed['probabilities'], 'confidence': routed['confidence'],
                    'latency_seconds': routed['latency_seconds'], 'cold_load': routed.get('cold_load'),
                    'load_seconds': routed.get('load_seconds'), 'inference_seconds': routed.get('inference_seconds'),
                    'needs_human_review': True, 'authorizes_execution': False})
            results[dataset_name][version] = metrics(predictions)
        del provider
        gc.collect()
    return results


def evaluate_frozen(directory, v1_development, provider_factory=FineTunedProvider):
    directory = Path(directory)
    destinations = {'heldout': directory / 'HELDOUT_EVALUATION.json',
                    'development': directory / 'DEVELOPMENT_REGRESSION.json'}
    if any(path.exists() for path in destinations.values()):
        raise ValueError('Preserve previous evaluation reports')
    selection_path = directory / 'MODEL_SELECTION.json'
    frozen = verify_selection(selection_path)
    extraction = read(directory / 'HOLDOUT_EXTRACTION.json')
    if datetime.fromisoformat(extraction['created_at']) < datetime.fromisoformat(frozen['created_at']):
        raise ValueError('Holdout was extracted before model selection')
    test_path = directory / 'test_raw.jsonl'
    if sha(test_path) != extraction['output_sha256']['test_raw.jsonl']:
        raise ValueError('Extracted test data changed')
    train = rows(directory / 'train_raw.jsonl')
    validation = rows(directory / 'validation_raw.jsonl')
    datasets = {'heldout': rows(test_path), 'development': rows(v1_development)}
    development_groups = {r['provenance']['group_id'] for r in train + validation}
    if development_groups & {r['provenance']['group_id'] for r in datasets['heldout']}:
        raise ValueError('Heldout source groups overlap training or validation')
    evaluated = evaluate_models(datasets, {'v1': frozen['v1_adapter'], 'selected_v2': frozen['selected']['adapter']}, provider_factory)
    verify_selection(selection_path)
    if sha(test_path) != extraction['output_sha256']['test_raw.jsonl']:
        raise ValueError('Test data changed during evaluation')
    for name, path in destinations.items():
        report = {'created_at': datetime.now(timezone.utc).isoformat(),
                  'evaluation_role': 'Post-selection heldout operational snapshot' if name == 'heldout' else 'Consumed V1 test reused for V2 development; NOT untouched test',
                  'selection_sha256': sha(selection_path), 'input_sha256': sha(test_path if name == 'heldout' else v1_development),
                  'models': evaluated[name], 'baselines': baseline_reports(datasets[name], train),
                  'production_gate': False, 'authorizes_execution': False, 'needs_human_review': True,
                  'limitations': ['Policy-imitation labels are not independent human ground truth.',
                     'Adjacent event snapshots are correlated; report independent source groups.',
                     'No confidence calibration or production/generalization claim.',
                     'Holdout assignment occurred after execution began and routine monitoring; it is not a fully prospective unseen experiment.',
                     'CPU model timing includes cold/warm differences; a small sample is not a latency benchmark.']}
        write_new(path, report)
    return {name: str(path) for name, path in destinations.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--select-only', action='store_true')
    mode.add_argument('--evaluate', action='store_true')
    parser.add_argument('--directory', type=Path, default=ROOT / 'outputs/chum_ops_training_v2_20261001')
    parser.add_argument('--v1-adapter', type=Path, default=ROOT / 'outputs/harness/models/chum-ops-lora')
    parser.add_argument('--v1-development', type=Path, default=ROOT / 'outputs/chum_ops_training_20261001/test.jsonl')
    args = parser.parse_args()
    if args.select_only:
        result = freeze_selection(args.directory, [args.directory / 'COVERAGE_REPORT.json', args.directory / 'BALANCED_REPORT.json'], args.v1_adapter)
        print(json.dumps({'selected': result['selected']['adapter'], 'macro_f1': result['selected']['validation_macro_f1']}))
    else:
        print(json.dumps(evaluate_frozen(args.directory, args.v1_development)))


if __name__ == '__main__':
    main()