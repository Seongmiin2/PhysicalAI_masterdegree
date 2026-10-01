"""Versioned operational corpus; inspected V1 test is development, not V2 test."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
HOLDOUT = 'outputs/chum_window_extension_20261001'
TASK_SPLITS = {
    'window-dry-run-ec69ebf1bd19': ('validation', 'dry-run'),
    'window-smoke-4ef00198a8c5': ('train', 'smoke'),
    'finetune-2f69c1f884114a299cb5e73cdbca0eeb': ('train', 'finetune-v1'),
}
STATE_LABELS = {'RUNNING': 'MONITOR_RUNNING', 'COMPLETE': 'REVIEW_COMPLETED',
                'COMPLETED': 'REVIEW_COMPLETED', 'PARTIAL': 'RESUME_INCOMPLETE',
                'FAILED': 'INVESTIGATE_FAILURE'}

def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()

def dump_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]

def input_text(row):
    return '\n'.join(m['content'] for m in row['messages'] if m['role'] == 'user')

def record(evidence, label, group, split, source, source_hash, locator, **metadata):
    return {'record_id': sha(compact({'group': group, 'locator': locator, 'evidence': evidence})),
            'label': label, 'split': split,
            'messages': [{'role': 'user', 'content': compact(evidence)},
                         {'role': 'assistant', 'content': compact({'next_action': label})}],
            'provenance': {'group_id': group, 'source_path': source, 'source_sha256': source_hash,
                           'locator': locator, 'kind': 'OBSERVED_REAL_EVENT', 'synthetic': False,
                           'label_origin': 'deterministic_operational_policy_v2',
                           'human_approved': False, 'scientific_ground_truth': False, **metadata}}

def lifecycle_record(event, split, mode, source):
    event_id, created, kind, task, payload = event
    payload = json.loads(payload) if isinstance(payload, str) else payload
    if kind == 'task_claimed':
        status = 'RUNNING'
    elif kind == 'task_finished' and payload.get('status') in ('completed', 'failed'):
        status = payload['status'].upper()
    else:
        return None
    # No outputs, target recommendations, worker identifiers, or model text.
    evidence = {'artifact_type': 'live_status_event', 'status': status, 'stage': 'task_lifecycle'}
    return record(evidence, STATE_LABELS[status], 'harness_task/' + task, split,
                  source, sha(compact(list(event))), f'events.id={event_id}',
                  event_created_at=created, lifecycle_mode=mode,
                  operational_scope='actual software task lifecycle; not a physical experiment state')

def audit_groups(splits):
    groups = {}
    for split, items in splits.items():
        for item in items:
            group = item['provenance']['group_id']
            if group in groups and groups[group] != split:
                raise ValueError('Run group leakage: ' + group)
            if HOLDOUT.split('/')[-1] in compact(item) and split != 'test':
                raise ValueError('Reserved holdout leaked into development')
            groups[group] = split
    return groups

def write_jsonl(path, items):
    with Path(path).open('x', encoding='utf-8') as stream:
        for item in items:
            serialized = dict(item)
            serialized.setdefault('text', input_text(item) if 'messages' in item else None)
            stream.write(compact(serialized) + '\n')

def normalize_rows(items):
    from providers.ops_features import canonical_text
    result = []
    for original in items:
        item = deepcopy(original)
        raw = input_text(item)
        item['raw_input'] = raw
        item['text'] = canonical_text(raw)
        item['messages'] = [{'role': 'user', 'content': canonical_text(raw)},
                            {'role': 'assistant', 'content': compact({'next_action': item['label']})}]
        item['provenance']['representation'] = 'canonical_factual_v2'
        result.append(item)
    return result

def build(output, database, v1):
    output, database, v1 = Path(output), Path(database), Path(v1)
    assignment = json.loads((output/'HOLDOUT_ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
    if assignment['holdout_root'] != HOLDOUT:
        raise ValueError('Unexpected holdout assignment')
    if (output/'DATASET_MANIFEST.json').exists():
        raise ValueError('Published V2 corpus is immutable')
    splits = {'train': [], 'validation': []}
    for old, new in [('train', 'train'), ('test', 'train'), ('validation', 'validation')]:
        for item in rows(v1/f'{old}.jsonl'):
            item['split'] = new
            item['provenance']['v1_split'] = old
            item['provenance']['development_reuse'] = old == 'test'
            splits[new].append(item)
    with sqlite3.connect(f'file:{database.resolve().as_posix()}?mode=ro', uri=True) as db:
        db.execute('BEGIN')
        cutoff = db.execute('SELECT MAX(id) FROM events').fetchone()[0] or 0
        placeholders = ','.join('?' for _ in TASK_SPLITS)
        events = db.execute(f"SELECT id,created_at,kind,task_id,payload FROM events WHERE id <= ? AND task_id IN ({placeholders}) AND kind IN ('task_claimed','task_finished') ORDER BY id", [cutoff, *TASK_SPLITS]).fetchall()
    used = []
    for event in events:
        split, mode = TASK_SPLITS[event[3]]
        item = lifecycle_record(event, split, mode, str(database.relative_to(ROOT)))
        if item:
            splits[split].append(item)
            used.append({'id': event[0], 'created_at': event[1], 'kind': event[2], 'task_id': event[3], 'payload': json.loads(event[4])})
    groups = audit_groups(splits)
    # Resolve canonicalization before publishing any corpus files.
    normalized = {split: normalize_rows(items) for split, items in splits.items()}
    for split in splits:
        write_jsonl(output/f'{split}_raw.jsonl', splits[split])
        write_jsonl(output/f'{split}_normalized.jsonl', normalized[split])
    write_jsonl(output/'SOURCE_EVENT_SNAPSHOT.jsonl', used)
    manifest = {'schema_version': 2, 'created_at': datetime.now(timezone.utc).isoformat(),
                'database_event_high_watermark': cutoff, 'holdout_extracted': False,
                'holdout_assignment_sha256': sha((output/'HOLDOUT_ASSIGNMENT.json').read_bytes()),
                'group_splits': groups, 'counts': {s: {'records': len(r), 'labels': dict(Counter(x['label'] for x in r)), 'groups': len({x['provenance']['group_id'] for x in r})} for s,r in splits.items()},
                'source_v1_sha256': {s: sha((v1/f'{s}.jsonl').read_bytes()) for s in ['train','validation','test']},
                'output_sha256': {p.name: sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))},
                'lifecycle_task_assignments': TASK_SPLITS, 'human_approved_labels': False,
                'production_ready': False, 'label_scope': 'operational policy imitation only',
                'limitations': ['V1 inspected test is reused as training development data, not untouched evaluation.',
                  'Dry-run/smoke records represent actual software lifecycle only, not physical experiments.',
                  'Validation live-format examples come from one software dry-run, not independent physical experiments.',
                  'RESUME_INCOMPLETE has only one training incident; REQUIRE_HUMAN_REVIEW remains absent.',
                  'Epoch snapshots and adjacent live states are correlated; report group counts.',
                  'Main holdout was assigned after execution started and routine status monitoring, before V2 extraction.',
                  'Source snapshot can contain task result metadata for audit; model input projects only factual lifecycle status.']}
    dump_new(output/'DATASET_MANIFEST.json', manifest)
    return manifest

def completed_result_record(path, reserved_root):
    """Published RESULT is an observed final artifact, not an inferred status."""
    path, reserved_root = Path(path).resolve(), Path(reserved_root).resolve()
    if path.name != 'RESULT.json' or path.parent.parent != reserved_root:
        raise ValueError('Final result must be a direct task child of the reserved root')
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or not {'epochs_run', 'test_evaluated', 'run_fingerprint'} <= value.keys():
        raise ValueError('Incomplete or unrecognized published result')
    evidence = {'artifact_type': 'published_final_result', 'task': path.parent.name,
                **{k: value[k] for k in ('architecture', 'variant', 'seed', 'window',
                    'epochs_run', 'best_epoch', 'best_validation_mse', 'test_evaluated') if k in value}}
    return record(evidence, 'REVIEW_COMPLETED', HOLDOUT.split('/')[-1], 'test', str(path),
                  sha(raw), 'json:root', kind='OBSERVED_REAL_ARTIFACT', kind_observation='atomically_published_final_result')


def extract_holdout(output, database, root=ROOT):
    """Call only once AFTER V2 checkpoint selection. Never called by build()."""
    output, database, root = Path(output), Path(database), Path(root)
    assignment = json.loads((output/'HOLDOUT_ASSIGNMENT.json').read_text(encoding='utf-8-sig'))
    if assignment['holdout_root'] != HOLDOUT or (output/'test_normalized.jsonl').exists():
        raise ValueError('Holdout assignment mismatch or already extracted')
    policy_path = output/'HOLDOUT_INCLUSION_POLICY.json'
    policy = json.loads(policy_path.read_text(encoding='utf-8'))
    if policy.get('holdout_root') != HOLDOUT:
        raise ValueError('Holdout inclusion policy mismatch')
    target = (root/HOLDOUT).resolve()
    retained = []
    with sqlite3.connect(f'file:{database.resolve().as_posix()}?mode=ro', uri=True) as db:
        db.execute('BEGIN')
        cutoff = db.execute('SELECT MAX(id) FROM events').fetchone()[0] or 0
        for event in db.execute("SELECT id,created_at,kind,task_id,payload FROM events WHERE id <= ? AND kind='artifact_updated' ORDER BY id", (cutoff,)):
            payload = json.loads(event[4])
            if not isinstance(payload.get('path'), str) or Path(payload['path']).resolve() != target/'LIVE_STATUS.json':
                continue
            state = json.loads(payload['content'])
            if state.get('status') not in STATE_LABELS:
                continue
            evidence = {'artifact_type': 'live_status_event', **{k: state[k] for k in ('status','stage','task','epoch','best_epoch','completed_tasks','error') if k in state}}
            retained.append(record(evidence, STATE_LABELS[state['status']], HOLDOUT.split('/')[-1], 'test', str(database), sha(compact(list(event))), f'events.id={event[0]}'))
    latest = target/'LIVE_STATUS.json'
    raw = latest.read_bytes()
    state = json.loads(raw)
    if state.get('status') in STATE_LABELS:
        evidence = {'artifact_type': 'live_status_event', **{k: state[k] for k in ('status','stage','task','epoch','best_epoch','completed_tasks','error') if k in state}}
        retained.append(record(evidence, STATE_LABELS[state['status']], HOLDOUT.split('/')[-1], 'test', str(latest), sha(raw), 'json:root'))
    for result_path in sorted(target.glob('*/RESULT.json')):
        retained.append(completed_result_record(result_path, target))
    unique = {}
    for item in retained:
        unique.setdefault(input_text(item), item)
    retained = list(unique.values())
    if not retained:
        raise ValueError('No genuine heldout statuses available')
    write_jsonl(output/'test_raw.jsonl', retained)
    write_jsonl(output/'test_normalized.jsonl', normalize_rows(retained))
    dump_new(output/'HOLDOUT_EXTRACTION.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'database_event_high_watermark': cutoff, 'count': len(retained), 'labels': dict(Counter(x['label'] for x in retained)), 'independent_groups': 1, 'inclusion_policy_sha256': sha(policy_path.read_bytes()), 'output_sha256': {p.name: sha(p.read_bytes()) for p in [output/'test_raw.jsonl', output/'test_normalized.jsonl']}})
    return retained

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(ROOT/'outputs/chum_ops_training_v2_20261001'))
    parser.add_argument('--database', default=str(ROOT/'outputs/harness/research.sqlite3'))
    parser.add_argument('--v1', default=str(ROOT/'outputs/chum_ops_training_20261001'))
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.database, args.v1)['counts'], indent=2))
