import sys
import unittest
import json
import tempfile
import pandas as pd
from pathlib import Path

import numpy as np
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'experiments'))
from run_chum_window_extension import build_model, target_indices, validate_config, experiment, run_task


class WindowExtensionTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        self.cfg = yaml.safe_load((ROOT/'configs/chum_window_extension.yaml').read_text(encoding='utf-8'))

    def test_earliest_sample_reaches_tcn_prediction(self):
        model = build_model(self.cfg, 'tcn', 'F1')
        # Positive weights avoid accidental cancellation or dead activation gradients.
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.fill_(0.01)
        sequence = torch.ones(1, 120, 52, requires_grad=True)
        model(sequence).sum().backward()
        self.assertGreater(float(sequence.grad[:, 0].abs().sum()), 0)
        self.assertGreaterEqual(model.receptive_field, 120)

    def test_all_windows_same_capacity_and_valid_gradients(self):
        for architecture in ('tcn', 'transformer'):
            model = build_model(self.cfg, architecture, 'F1')
            counts = []
            for window in self.cfg['windows']:
                x = torch.randn(2, window, 52, requires_grad=True)
                prediction = model(x)
                self.assertEqual(tuple(prediction.shape), (2, 41))
                prediction.square().mean().backward()
                self.assertTrue(torch.isfinite(x.grad).all())
                counts.append(sum(p.numel() for p in model.parameters()))
            self.assertEqual(len(set(counts)), 1)
        with self.assertRaises(ValueError):
            model(torch.randn(1, 121, 52))

    def test_common_targets_and_no_future_leak(self):
        features = np.arange(200*52, dtype=np.float32).reshape(1, 200, 52)
        targets = target_indices(self.cfg, 'validation')
        self.assertEqual(targets[0], 120)
        self.assertEqual(targets[-1]+1, experiment.FAULT_ONSET-1)
        for window in self.cfg['windows']:
            ds = experiment.WindowDataset(features, np.array([0]), targets[:1], window, True,
                                          np.zeros(52, np.float32), np.ones(52, np.float32))
            x, y, _, sample = ds[0]
            self.assertEqual(sample, 121)
            np.testing.assert_array_equal(x[-1], features[0, 119])
            np.testing.assert_array_equal(y, features[0, 120, :41])
            self.assertEqual(len(x), window)

    def test_identical_control_capacity_keeps_seeded_initialization(self):
        torch.manual_seed(47)
        baseline = build_model(self.cfg, 'transformer', 'F0')
        torch.manual_seed(47)
        control = build_model(self.cfg, 'transformer', 'F0-C')
        for name, tensor in baseline.state_dict().items():
            self.assertTrue(torch.equal(tensor, control.state_dict()[name]))

    def test_validation_only_training_writes_complete_result_atomically(self):
        cfg = dict(self.cfg, device='cpu', epochs=1, min_epochs=1, evaluate_test=False)
        split = pd.DataFrame({'split': ['train', 'validation'], 'run_index': [0, 1]})
        features = np.random.default_rng(0).normal(size=(2, 600, 52)).astype(np.float32)
        updates = []
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(cfg, 'tcn', 'F1', 47, 120, split, features,
                              np.zeros(52, np.float32), np.ones(52, np.float32),
                              Path(temporary), lambda **values: updates.append(values), 'synthetic-test')
            folder = Path(temporary)/'tcn_F1_seed47_window120'
            saved = json.loads((folder/'RESULT.json').read_text(encoding='utf-8'))
            self.assertEqual(saved, result)
            self.assertEqual(saved['run_fingerprint'], 'synthetic-test')
            self.assertFalse(saved['test_evaluated'])
            self.assertNotIn('auroc', saved)
            self.assertTrue((folder/'best.pt').is_file())
            self.assertFalse((folder/'RESULT.tmp').exists())
            self.assertEqual(saved['best_epoch'], 1)
            self.assertEqual(updates[-1]['stage'], 'calibration')

    def test_invalid_coverage_rejected(self):
        self.cfg['tcn_layers'] = 2
        with self.assertRaises(ValueError):
            validate_config(self.cfg)

    def test_capacity_control_keeps_attention_heads(self):
        for architecture in ('tcn', 'transformer'):
            f1 = build_model(self.cfg, architecture, 'F1')
            control = build_model(self.cfg, architecture, 'F0-C')
            target = sum(p.numel() for p in f1.parameters())
            actual = sum(p.numel() for p in control.parameters())
            self.assertLess(abs(actual-target)/target, 0.05)
            if architecture == 'transformer':
                self.assertEqual(control.encoder.layers[0].self_attn.num_heads, 4)


if __name__ == '__main__':
    unittest.main()
