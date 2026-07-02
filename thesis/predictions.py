from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from thesis.metrics import compute_binary_metrics


VERIFIED_METRICS = (
    "sensitivity",
    "specificity",
    "balanced_accuracy",
    "roc_auc",
)


def save_prediction_scores(
    path: str | Path,
    labels,
    probabilities,
    logits,
    sample_ids,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        y_true=np.asarray(labels, dtype=np.int64),
        y_score=np.asarray(probabilities, dtype=np.float64),
        y_logit=np.asarray(logits, dtype=np.float64),
        sample_id=np.asarray(sample_ids, dtype=str),
    )


def verify_prediction_metrics(
    prediction_npz: str | Path,
    aggregate_json: str | Path,
    tolerance: float = 1e-6,
    metrics_key: str | None = None,
) -> dict[str, float | int | None]:
    with np.load(prediction_npz) as payload:
        y_true = payload["y_true"]
        y_score = payload["y_score"]
    aggregate = json.loads(Path(aggregate_json).read_text())
    if metrics_key is not None:
        for key in metrics_key.split("."):
            aggregate = aggregate[key]
    metrics = compute_binary_metrics(y_true, y_score, threshold=0.5)

    divergences = []
    for metric in VERIFIED_METRICS:
        actual = metrics.get(metric)
        expected = aggregate.get(metric)
        if actual is None or expected is None:
            if actual != expected:
                divergences.append(f"{metric}: npz={actual!r} json={expected!r}")
            continue
        if abs(float(actual) - float(expected)) > tolerance:
            divergences.append(f"{metric}: npz={actual} json={expected}")

    if divergences:
        raise AssertionError("; ".join(divergences))
    return {"num_samples": int(len(y_true)), **{metric: metrics.get(metric) for metric in VERIFIED_METRICS}}
