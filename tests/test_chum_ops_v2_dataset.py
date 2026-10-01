import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ops_v2_builder', ROOT/'experiments/build_chum_ops_v2_dataset.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class V2DatasetTests(unittest.TestCase):
    def test_lifecycle_projection_excludes_model_outputs(self):
        event = (1, 'now', 'task_finished', 'task', json.dumps({'status': 'completed', 'result': {'next_action': 'FORGED_TARGET', 'score': 1}, 'worker_id': 'secret-worker'}))
        row = builder.lifecycle_record(event, 'train', 'smoke', 'db')
        evidence = json.loads(builder.input_text(row))
        self.assertEqual(evidence, {'artifact_type': 'live_status_event', 'status': 'COMPLETED', 'stage': 'task_lifecycle'})
        self.assertEqual(row['label'], 'REVIEW_COMPLETED')
        self.assertFalse(row['provenance']['human_approved'])
        self.assertEqual(row['provenance']['lifecycle_mode'], 'smoke')

    def test_pending_and_blocked_not_invented_as_human_labels(self):
        for kind, payload in [('task_created', {}), ('task_finished', {'status': 'blocked'})]:
            self.assertIsNone(builder.lifecycle_record((1,'now',kind,'x',payload), 'train','dry-run','db'))

    def test_whole_group_leakage_rejected(self):
        row = {'provenance': {'group_id': 'same-physical-run'}}
        with self.assertRaisesRegex(ValueError, 'group leakage'):
            builder.audit_groups({'train': [row], 'validation': [row]})

    def test_reserved_holdout_child_rejected(self):
        row = {'provenance': {'group_id': 'other', 'source_path': builder.HOLDOUT+'/child/RESULT.json'}}
        with self.assertRaisesRegex(ValueError, 'holdout leaked'):
            builder.audit_groups({'train': [row]})

    def test_immutable_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'assignment.json'
            builder.dump_new(path, {'value': 1})
            with self.assertRaises(FileExistsError):
                builder.dump_new(path, {'value': 2})
            self.assertEqual(json.loads(path.read_text())['value'], 1)

    def test_final_artifact_projection_and_reserved_group(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'reserved'
            path = root/'task'/'RESULT.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'epochs_run': 50, 'test_evaluated': True,
                'run_fingerprint': 'run-hash', 'next_action': 'FORGED', 'auroc': 0.99}))
            item = builder.completed_result_record(path, root)
            evidence = json.loads(builder.input_text(item))
            self.assertEqual(item['label'], 'REVIEW_COMPLETED')
            self.assertEqual(item['provenance']['group_id'], builder.HOLDOUT.split('/')[-1])
            self.assertEqual(item['provenance']['kind'], 'OBSERVED_REAL_ARTIFACT')
            self.assertEqual(evidence['artifact_type'], 'published_final_result')
            self.assertNotIn('status', evidence)
            self.assertNotIn('auroc', evidence)
            self.assertNotIn('next_action', evidence)
            with self.assertRaisesRegex(ValueError, 'reserved root'):
                builder.completed_result_record(path, root/'other')

    def test_normalization_does_not_see_label(self):
        evidence = {'artifact_type': 'live_status_event', 'status': 'RUNNING'}
        a = builder.record(evidence, 'MONITOR_RUNNING', 'a', 'train', 'db', 'hash', 'id1')
        b = builder.record(evidence, 'REVIEW_COMPLETED', 'a', 'train', 'db', 'hash', 'id1')
        norm_a, norm_b = builder.normalize_rows([a,b])
        self.assertEqual(builder.input_text(norm_a), builder.input_text(norm_b))
        self.assertNotIn('MONITOR_RUNNING', builder.input_text(norm_a))
        self.assertIn('RUNNING', builder.input_text(norm_a))


if __name__ == '__main__':
    unittest.main()
