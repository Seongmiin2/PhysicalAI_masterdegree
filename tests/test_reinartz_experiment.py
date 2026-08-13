import numpy as np

from src.experiments.reinartz_f0_f1 import persistence_delays


def test_persistence_alarm_requires_consecutive_exceedances() -> None:
    scores = np.zeros(20)
    scores[[2, 4, 6]] = 2.0
    scores[12:15] = 2.0
    runs = np.ones(20, dtype=int)
    samples = np.arange(590, 610)
    detected, delay, prealarm = persistence_delays(scores, runs, samples, 1.0, 3)
    assert detected == 1.0
    assert delay == 4.0
    assert prealarm == 0.0
