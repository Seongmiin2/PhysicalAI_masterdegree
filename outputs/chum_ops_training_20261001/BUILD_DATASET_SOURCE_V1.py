"""Build audited operational-policy training records from real CHUM artifacts.

Labels are deterministic workflow heuristics, not human-approved scientific truth.
No synthetic failures, fabricated runs, or model-generated answers are included.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = ['INVESTIGATE_FAILURE', 'MONITOR_RUNNING', 'RESUME_INCOMPLETE',
           'REVIEW_COMPLETED', 'REQUIRE_HUMAN_REVIEW']
POLICY = {
    'INVESTIGATE_FAILURE': 'A real error or failed task event requires investigation.',
    'MONITOR_RUNNING': 'An explicit running observation, or an epoch-only historical snapshot without finalization, requires monitoring.',
    'RESUME_INCOMPLETE': 'An explicit PARTIAL task-budget stop indicates remaining work to resume.',
    'REVIEW_COMPLETED': 'A completed task or published final result requires result review, not scientific acceptance.',
    'REQUIRE_HUMAN_REVIEW': 'An explicit pending human decision requires human review; no such reliable labeled samples are invented.',
}
SYSTEM = 'Classify the next operational action from the supplied CHUM evidence. Return JSON with next_action. This is workflow triage, not scientific approval or command execution.'


def digest(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def compact_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def group_and_split(experiment, task=''):
    if experiment == 'chum_window_pilot_20261001':
        return experiment, 'test'
    # Identical Transformer F0/F0-C runs share a group, even though saved separately.
    canonical = task.replace('transformer_F0-C_', 'transformer_F0_')
    group = experiment + ('/' + canonical if canonical else '')
    if experiment == 'chum_training_budget_20260921' and task in ('tcn_F1_seed47', 'transformer_F1_seed47'):
        return group, 'validation'
    return group, 'train'


def choose_epochs(rows, limit=8):
    if len(rows) <= limit:
        return list(enumerate(rows, 2))
    indexes = sorted({round(i*(len(rows)-1)/(limit-1)) for i in range(limit)})
    return [(i+2, rows[i]) for i in indexes]


def build(output, database):
    output.mkdir(parents=True, exist_ok=True)
    if (output/'DATASET_MANIFEST.json').exists():
        raise ValueError('Dataset is immutable after publication; choose a new --output')
    records, sources, seen = [], {}, set()

    def read_source(path):
        raw = path.read_bytes()
        key = str(path.relative_to(ROOT))
        sources[key] = {'sha256': digest(raw), 'size_bytes': len(raw)}
        return key, raw.decode('utf-8-sig')

    def add(evidence, label, group, split, source, source_hash, locator, provenance_kind):
        # Semantically identical snapshots are kept once inside a group.
        identity = digest(compact_json({'group': group, 'evidence': evidence}))
        if identity in seen:
            return
        seen.add(identity)
        records.append({'record_id': identity, 'label': label, 'split': split,
                        'messages': [{'role': 'system', 'content': SYSTEM},
                                     {'role': 'user', 'content': compact_json(evidence)},
                                     {'role': 'assistant', 'content': compact_json({'next_action': label})}],
                        'provenance': {'source_path': source, 'source_sha256': source_hash,
                                       'locator': locator, 'group_id': group,
                                       'kind': provenance_kind, 'synthetic': False,
                                       'label_origin': 'deterministic_operational_policy_v1',
                                       'human_approved': False, 'scientific_ground_truth': False}})

    # Assign run groups before sampling epochs or extracting final result records.
    for name in ('chum_training_budget_20260921', 'chum_window_pilot_20261001'):
        directory = ROOT/'outputs'/name
        for history in sorted(directory.glob('*/TRAINING_HISTORY.csv')):
            group, split = group_and_split(name, history.parent.name)
            source, content = read_source(history)
            for line, row in choose_epochs(list(csv.DictReader(io.StringIO(content)))):
                evidence = {'artifact_type': 'historical_training_epoch', 'task': history.parent.name,
                            'snapshot_semantics': 'Epoch metrics only; current run status is not inferred.',
                            'epoch': int(row['epoch']), 'train_mse': float(row['train_mse']),
                            'validation_mse': float(row['validation_mse']), 'best_epoch': int(row['best_epoch'])}
                add(evidence, 'MONITOR_RUNNING', group, split, source, sources[source]['sha256'],
                    f'csv_line:{line}', 'DERIVED_FROM_REAL_ARTIFACT')
            result_path = history.parent/'RESULT.json'
            if result_path.exists():
                source, content = read_source(result_path)
                row = json.loads(content)
                evidence = {'artifact_type': 'published_final_result', 'task': history.parent.name,
                            **{key: row[key] for key in ('architecture', 'variant', 'seed', 'window',
                               'epochs_run', 'best_epoch', 'best_validation_mse', 'test_evaluated') if key in row}}
                add(evidence, 'REVIEW_COMPLETED', group, split, source, sources[source]['sha256'],
                    'json:root', 'OBSERVED_REAL_ARTIFACT')

    # Read only canonical final metrics, excluding partial/copied/per-fault tables.
    metrics = ROOT/'outputs/chum_seed47_20260921/training/G2_METRICS.csv'
    source, content = read_source(metrics)
    for line, row in enumerate(csv.DictReader(io.StringIO(content)), 2):
        task = f"{row['architecture']}_{row['variant']}_seed{row['seed']}"
        group, split = group_and_split('chum_seed47_20260921', task)
        evidence = {'artifact_type': 'published_final_metrics', 'task': task,
                    'architecture': row['architecture'], 'variant': row['variant'],
                    'epochs': int(row['epochs']), 'parameters': int(row['parameters']),
                    'elapsed_seconds': float(row['elapsed_seconds'])}
        add(evidence, 'REVIEW_COMPLETED', group, split, source, sources[source]['sha256'],
            f'csv_line:{line}', 'OBSERVED_REAL_ARTIFACT')

    # Database events are snapshotted inside one read transaction. Synthetic smoke
    # and dry-run executions are excluded, even though the processes really ran.
    database_uri = f'file:{database.resolve().as_posix()}?mode=ro'
    with sqlite3.connect(database_uri, uri=True) as connection:
        connection.execute('BEGIN')
        event_rows = connection.execute('SELECT id,created_at,kind,task_id,payload FROM events ORDER BY id').fetchall()
        high_watermark = max((row[0] for row in event_rows), default=0)
    used_events = []
    for event_id, created_at, kind, task_id, payload_text in event_rows:
        payload = json.loads(payload_text)
        source = str(database.relative_to(ROOT))
        event_identity = digest(compact_json([event_id, created_at, kind, task_id, payload]))
        if kind == 'agent_failed':
            evidence = {'artifact_type': 'agent_failure_event', 'agent': payload.get('agent'),
                        'error': payload.get('error'), 'latency_seconds': payload.get('latency_seconds')}
            group = 'harness_request/' + payload['request_id']
            add(evidence, 'INVESTIGATE_FAILURE', group, 'train', source, event_identity,
                f'events.id={event_id}', 'OBSERVED_REAL_EVENT')
            used_events.append({'id': event_id, 'created_at': created_at, 'kind': kind, 'task_id': task_id, 'payload': payload})
        elif kind == 'artifact_updated' and task_id and task_id.startswith('window-pilot-'):
            if not payload.get('path', '').replace('\\', '/').endswith('/LIVE_STATUS.json'):
                continue
            status = json.loads(payload['content'])
            state = status.get('status')
            label = {'RUNNING': 'MONITOR_RUNNING', 'PARTIAL': 'RESUME_INCOMPLETE',
                     'FAILED': 'INVESTIGATE_FAILURE', 'COMPLETE': 'REVIEW_COMPLETED'}.get(state)
            if label is None:
                continue
            evidence = {'artifact_type': 'live_status_event', **{key: status[key] for key in
                        ('status', 'stage', 'task', 'epoch', 'best_epoch', 'completed_tasks', 'error') if key in status}}
            add(evidence, label, 'chum_window_pilot_20261001', 'test', source, event_identity,
                f'events.id={event_id}', 'OBSERVED_REAL_EVENT')
            used_events.append({'id': event_id, 'created_at': created_at, 'kind': kind, 'task_id': task_id, 'payload': payload})

    # Latest status can be newer than the database watcher. Semantic dedup keeps
    # it only if this exact state has not already been observed in the DB snapshot.
    status_path = ROOT/'outputs/chum_window_pilot_20261001/LIVE_STATUS.json'
    if status_path.exists():
        source, content = read_source(status_path)
        status = json.loads(content)
        label = {'RUNNING': 'MONITOR_RUNNING', 'PARTIAL': 'RESUME_INCOMPLETE',
                 'FAILED': 'INVESTIGATE_FAILURE', 'COMPLETE': 'REVIEW_COMPLETED'}.get(status.get('status'))
        if label:
            evidence = {'artifact_type': 'live_status_event', **{key: status[key] for key in
                        ('status', 'stage', 'task', 'epoch', 'best_epoch', 'completed_tasks', 'error') if key in status}}
            add(evidence, label, 'chum_window_pilot_20261001', 'test', source, sources[source]['sha256'],
                'json:root', 'OBSERVED_REAL_ARTIFACT')

    group_splits = {}
    for record in records:
        group = record['provenance']['group_id']
        if group in group_splits and group_splits[group] != record['split']:
            raise AssertionError('Group leakage detected')
        group_splits[group] = record['split']
    counts, hashes = {}, {}
    for split in ('train', 'validation', 'test'):
        selected = [r for r in records if r['split'] == split]
        path = output/f'{split}.jsonl'
        path.write_text(''.join(compact_json(r)+'\n' for r in selected), encoding='utf-8')
        counts[split] = {'records': len(selected), 'labels': dict(Counter(r['label'] for r in selected)),
                         'provenance_kinds': dict(Counter(r['provenance']['kind'] for r in selected))}
        hashes[path.name] = digest(path.read_bytes())
    (output/'SOURCE_EVENT_SNAPSHOT.jsonl').write_text(''.join(compact_json(r)+'\n' for r in used_events), encoding='utf-8')
    manifest = {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                'purpose': 'Operational policy imitation from project artifacts; not scientific decision correctness.',
                'labels': ACTIONS, 'label_definitions': POLICY, 'counts': counts,
                'group_splits': group_splits, 'split_unit': 'whole model run; entire current pilot held out',
                'source_files': sources, 'output_sha256': hashes, 'database_event_high_watermark': high_watermark,
                'synthetic_records': 0, 'human_approved_labels': False,
                'max_epoch_snapshots_per_model_run': 8, 'production_ready': False,
                'limitations': ['Small correlated operational corpus; accuracy is not evidence of scientific judgment.',
                  'Historical epoch records are DERIVED_FROM_REAL_ARTIFACT policy cases, not actual historical live statuses.',
                  'Labels are deterministic heuristic policy assignments, not user or supervisor approvals.',
                  'No reliable REQUIRE_HUMAN_REVIEW examples; RESUME_INCOMPLETE may appear only in held-out pilot.',
                  'Missing/rare training classes cannot be claimed learned; all outputs require deterministic policy gating.',
                  'Temporal pilot holdout is a single run, not independent broad operational generalization.',
                  'Identical Transformer F0/F0-C initialization family kept in one split; no copied partial metrics included.']}
    (output/'DATASET_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'counts': counts, 'groups': len(group_splits), 'output': str(output)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='outputs/chum_ops_training_20261001')
    parser.add_argument('--database', default='outputs/harness/research.sqlite3')
    args = parser.parse_args()
    build(ROOT/args.output, ROOT/args.database)
