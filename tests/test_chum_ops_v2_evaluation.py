import json
from pathlib import Path

import pytest

from experiments.evaluate_chum_ops_v2 import (
    baseline_reports, evaluate_models, freeze_selection, metrics,
    select_candidate, sha, verify_selection,
)


def make_candidate(tmp_path, name, macro, loss):
    adapter = tmp_path / (name + '_adapter')
    adapter.mkdir()
    for file in ('adapter_model.safetensors', 'adapter_config.json', 'router_config.json'):
        (adapter / file).write_bytes(name.encode())
    report = tmp_path / (name + '.json')
    report.write_text(json.dumps({
        'config': {'output': str(adapter)}, 'adapter_sha256': sha(adapter / 'adapter_model.safetensors'),
        'selected_validation': {'macro_f1': macro, 'loss': loss}, 'selected_epoch': 1,
    }), encoding='utf-8')
    return report, adapter


def test_validation_f1_then_loss_selects_without_test(tmp_path):
    coverage, _ = make_candidate(tmp_path, 'coverage', 0.6, 0.1)
    balanced, _ = make_candidate(tmp_path, 'balanced', 0.7, 0.8)
    assert select_candidate([coverage, balanced])[1]['report'] == str(balanced)
    report = json.loads(balanced.read_text())
    report['selected_validation']['macro_f1'] = 0.6
    balanced.write_text(json.dumps(report))
    assert select_candidate([coverage, balanced])[1]['report'] == str(coverage)


def test_test_consumed_candidate_is_rejected(tmp_path):
    path, _ = make_candidate(tmp_path, 'candidate', 0.6, 0.1)
    report = json.loads(path.read_text())
    report['heldout_test'] = {'accuracy': 1.0}
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='test evaluation'):
        select_candidate([path])


def test_selection_freeze_detects_mutation_and_refuses_extracted_test(tmp_path):
    report, adapter = make_candidate(tmp_path, 'candidate', 0.6, 0.1)
    for name in ('train_raw.jsonl', 'validation_raw.jsonl', 'train_normalized.jsonl', 'validation_normalized.jsonl', 'DATASET_MANIFEST.json',
                 'HOLDOUT_ASSIGNMENT.json', 'HOLDOUT_INCLUSION_POLICY.json'):
        (tmp_path / name).write_text('{}', encoding='utf-8')
    freeze_selection(tmp_path, [report], adapter)
    frozen = verify_selection(tmp_path / 'MODEL_SELECTION.json')
    assert any(path.endswith('build_chum_ops_v2_dataset.py') for path in frozen['code_files'])
    assert any(path.endswith('finetune_chum_ops_v2.py') for path in frozen['code_files'])
    assert str(tmp_path / 'train_normalized.jsonl') in frozen['data_files']
    original_normalized = (tmp_path / 'train_normalized.jsonl').read_text()
    (tmp_path / 'train_normalized.jsonl').write_text('mutated training input')
    with pytest.raises(ValueError, match='changed'):
        verify_selection(tmp_path / 'MODEL_SELECTION.json')
    (tmp_path / 'train_normalized.jsonl').write_text(original_normalized)
    (adapter / 'router_config.json').write_text('changed')
    with pytest.raises(ValueError, match='changed'):
        verify_selection(tmp_path / 'MODEL_SELECTION.json')
    (tmp_path / 'test_raw.jsonl').write_text('{}')
    with pytest.raises(ValueError, match='before test extraction'):
        freeze_selection(tmp_path, [report], adapter)


def row(identifier, status, label):
    return {'record_id': identifier, 'label': label,
            'messages': [{'role': 'user', 'content': json.dumps({'artifact_type': 'live_status_event', 'status': status})}],
            'provenance': {'group_id': 'source_run'}}


def test_full_schema_macro_and_supported_macro_are_distinct():
    result = metrics([{'expected': 'MONITOR_RUNNING', 'predicted': 'MONITOR_RUNNING',
                       'artifact_type': 'live_status_event', 'group_id': 'run'}])
    assert result['macro_f1_full_five_actions'] == 0.2
    assert result['macro_f1_supported_classes'] == 1.0
    assert result['independent_groups'] == 1


def test_models_receive_identical_raw_records_and_rule_baseline():
    records = [row('one', 'RUNNING', 'MONITOR_RUNNING'), row('two', 'PARTIAL', 'RESUME_INCOMPLETE')]
    calls = {}
    class FakeProvider:
        def __init__(self, adapter_path, device):
            assert device == 'cpu'
            self.name = adapter_path
            calls[self.name] = []
        def route(self, record):
            calls[self.name].append(record['record_id'])
            return {'next_action': 'MONITOR_RUNNING', 'confidence': 0.5,
                    'probabilities': {'MONITOR_RUNNING': 0.5}, 'latency_seconds': 0.01}
    results = evaluate_models({'heldout': records}, {'v1': 'first', 'v2': 'second'}, FakeProvider)
    assert calls['first'] == calls['second'] == ['one', 'two']
    assert results['heldout']['v1']['accuracy'] == 0.5
    baseline = baseline_reports(records, [records[0]])
    assert baseline['observed_state_rule']['accuracy'] == 1.0
    assert baseline['majority_train']['accuracy'] == 0.5