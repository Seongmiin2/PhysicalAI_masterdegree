import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ops_builder', ROOT/'experiments/build_chum_ops_dataset.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class DatasetBuilderTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.gettempdir())/'chum-dataset-builder-test'
        self.pilot = self.root/'outputs/chum_window_pilot_20261001/LIVE_STATUS.json'

    def test_exact_pilot_path_accepted_independent_of_task_prefix(self):
        self.assertTrue(builder.is_pilot_status_event('artifact_updated', 'arbitrary-real-task',
                        {'path': str(self.pilot)}, self.root))

    def test_main_profile_reusing_pilot_prefix_is_rejected(self):
        path = self.root/'outputs/chum_window_extension_20261001/LIVE_STATUS.json'
        self.assertFalse(builder.is_pilot_status_event('artifact_updated', 'window-pilot-shared-prefix',
                         {'path': str(path)}, self.root))

    def test_sibling_or_training_history_cannot_enter_pilot_statuses(self):
        for path in (self.pilot.parent/'TRAINING_HISTORY.csv',
                     self.root/'outputs/chum_window_pilot_20261001_copy/LIVE_STATUS.json',
                     self.pilot.parent/'..'/'chum_window_extension_20261001'/'LIVE_STATUS.json'):
            self.assertFalse(builder.is_pilot_status_event('artifact_updated', 'window-pilot-x',
                             {'path': str(path)}, self.root))

    def test_non_artifact_or_missing_task_and_path_rejected(self):
        for kind, task, payload in [('task_finished','window-pilot-x',{'path':str(self.pilot)}),
                                    ('artifact_updated',None,{'path':str(self.pilot)}),
                                    ('artifact_updated','window-pilot-x',{}),
                                    ('artifact_updated','window-pilot-x',{'path':None})]:
            self.assertFalse(builder.is_pilot_status_event(kind, task, payload, self.root))

    def test_published_dataset_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifest = output/'DATASET_MANIFEST.json'
            manifest.write_text('{"frozen":true}')
            before = manifest.read_bytes()
            with self.assertRaises(ValueError):
                builder.build(output, output/'nonexistent.sqlite3')
            self.assertEqual(before, manifest.read_bytes())

    def test_frozen_v1_outputs_still_match_published_hashes(self):
        output = ROOT/'outputs/chum_ops_training_20261001'
        manifest = json.loads((output/'DATASET_MANIFEST.json').read_text(encoding='utf-8'))
        for name, expected in manifest['output_sha256'].items():
            self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()
