"""Binary ranking metrics with score ties evaluated as whole groups."""
from __future__ import annotations

import numpy as np


def binary_metrics(labels: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    """Return ROC AUC and non-interpolated average precision.

    Both classes must be present. Reject non-finite scores and labels outside
    {0, 1}; averaging arbitrary tie order would bias both ranking metrics.
    """
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=np.float64)
    if labels.ndim != 1 or scores.ndim != 1 or len(labels) != len(scores) or not len(labels):
        raise ValueError("labels and scores must be nonempty equal-length vectors")
    if not np.all(np.isfinite(scores)) or not np.all(np.isin(labels, [0, 1])):
        raise ValueError("Scores must be finite and labels must be binary")
    positive = labels == 1
    n_positive = int(positive.sum())
    n_negative = len(labels) - n_positive
    if not n_positive or not n_negative:
        raise ValueError("Both positive and negative examples are required")
    order = np.argsort(-scores, kind="stable")
    ordered_scores, ordered_positive = scores[order], positive[order]
    # Evaluate only at the end of a tied group, where a real threshold can fall.
    ends = np.r_[np.flatnonzero(np.diff(ordered_scores)), len(scores) - 1]
    true_positive = np.cumsum(ordered_positive, dtype=np.float64)[ends]
    predicted_positive = ends + 1
    false_positive = predicted_positive - true_positive
    tpr = np.r_[0.0, true_positive / n_positive]
    fpr = np.r_[0.0, false_positive / n_negative]
    auroc = np.sum(np.diff(fpr) * (tpr[:-1] + tpr[1:]) / 2)
    average_precision = np.sum(np.diff(tpr) * true_positive / predicted_positive)
    return float(auroc), float(average_precision)
