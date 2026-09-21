import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
from run_chum_training_budget import EarlyStop, censored_delays, experiment

class TrainingBudgetTests(unittest.TestCase):
    def test_best_checkpoint_updates_even_below_patience_delta(self):
        stop=EarlyStop(patience=2,min_delta=0.001,min_epochs=1)
        self.assertEqual(stop.update(1.0,1),(True,False))
        self.assertEqual(stop.update(0.9,2),(True,False))
        self.assertEqual(stop.update(0.8999,3),(True,False))
        self.assertEqual(stop.update(0.89995,4),(False,True))
        self.assertEqual(stop.best_epoch,3)
        self.assertEqual(stop.best,0.8999)

    def test_minimum_training_and_nonfinite_loss(self):
        stop=EarlyStop(patience=2,min_delta=0.001,min_epochs=4)
        self.assertFalse(stop.update(1,1)[1])
        self.assertFalse(stop.update(1,2)[1])
        self.assertFalse(stop.update(1,3)[1])
        self.assertTrue(stop.update(1,4)[1])
        with self.assertRaises(ValueError):
            stop.update(float('nan'),5)

    def test_missed_run_is_included_in_censored_delay(self):
        samples=np.tile(np.arange(598,605),2)
        runs=np.repeat([1,2],7)
        scores=np.array([0,0,1,1,1,1,1,0,0,0,0,0,0,0])
        self.assertEqual(censored_delays(scores,runs,samples,0.5,3),3.5)

    def test_training_window_excludes_prediction_target(self):
        features=np.zeros((1,30,52),dtype=np.float32)
        features[0,20,:]=99
        data=experiment.WindowDataset(features,np.array([0]),np.array([20]),20,True,np.zeros(52,dtype=np.float32),np.ones(52,dtype=np.float32))
        x,y,run,sample=data[0]
        self.assertEqual(tuple(x.shape),(20,52))
        self.assertEqual(float(x.sum()),0)
        self.assertTrue(bool((y==99).all()))
        self.assertEqual(sample,21)

if __name__=='__main__':
    unittest.main()
