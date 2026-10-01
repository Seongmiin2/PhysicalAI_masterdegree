import numpy as np
import pytest

from experiments.window_metrics import binary_metrics


def test_known_rankings():
    assert binary_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == (1.0, 1.0)
    assert binary_metrics([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]) == pytest.approx((0.0, 5 / 12))
    assert binary_metrics([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]) == pytest.approx((0.75, 5 / 6))


def test_constant_scores_and_permutation_invariance():
    labels = np.array([1, 0, 0, 0])
    assert binary_metrics(labels, np.ones(4)) == (0.5, 0.25)
    labels = np.array([0, 1, 1, 0, 1, 0])
    scores = np.array([0.9, 0.9, 0.5, 0.5, 0.2, 0.1])
    baseline = binary_metrics(labels, scores)
    # Mixed leading and middle tie groups give AUC=5/9, AP=8/15.
    assert baseline == pytest.approx((5 / 9, 8 / 15))
    rng = np.random.default_rng(47)
    for _ in range(20):
        order = rng.permutation(len(labels))
        assert binary_metrics(labels[order], scores[order]) == baseline


@pytest.mark.parametrize("labels,scores", [
    ([], []), ([0], [1]), ([1], [1]), ([0, 1], [1]),
    ([0, 1], [0, float("nan")]), ([0, 1], [0, float("inf")]),
    ([0, 2], [0, 1]), ([0, 0.5], [0, 1]), ([[0, 1]], [[0, 1]]),
])
def test_invalid_inputs(labels, scores):
    with pytest.raises(ValueError):
        binary_metrics(labels, scores)
