from __future__ import annotations

"""Temperature scaling for post-hoc binary calibration.

Temperature T is fit on a validation set and applied unchanged to test sets.
Because T > 0 rescales pre-sigmoid logits monotonically, ROC-AUC must remain
invariant. The positive class is Pneumonia=1. Inputs are pre-sigmoid logits.
"""

import csv
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy.optimize import minimize_scalar
from sklearn.metrics import roc_auc_score

from thesis.calibration import brier_score, ece
from thesis.metrics_canonical import load_npz_predictions, metrics_from_npz


FIELDNAMES = [
    "model",
    "dataset",
    "T",
    "ece_width_before",
    "ece_width_after",
    "ece_mass_before",
    "ece_mass_after",
    "ece_delta",
    "brier_before",
    "brier_after",
    "maxp_before",
    "maxp_after",
    "frac_prob_gt_099_before",
    "frac_prob_gt_099_after",
    "auc",
]


def _bce_with_logits(logits: np.ndarray, y: np.ndarray) -> float:
    """Numerically stable binary NLL for pre-sigmoid logits."""
    z = np.asarray(logits, dtype=float)
    labels = np.asarray(y, dtype=float)
    if z.shape != labels.shape:
        raise ValueError("logits and y must have the same shape")
    return float(np.mean(np.maximum(z, 0.0) - z * labels + np.log1p(np.exp(-np.abs(z)))))


def fit_temperature(
    val_logits: np.ndarray,
    val_y: np.ndarray,
    bounds: tuple[float, float] = (0.05, 10.0),
) -> float:
    """Fit T > 0 by minimizing validation NLL of val_logits / T.

    T > 1 indicates overconfidence and softens probabilities. T < 1 indicates
    underconfidence and sharpens probabilities.
    """
    logits = np.asarray(val_logits, dtype=float)
    labels = np.asarray(val_y, dtype=int)
    if logits.ndim != 1:
        raise ValueError("expected 1-D binary logits for the positive class")
    if logits.shape[0] != labels.shape[0]:
        raise ValueError("val_logits and val_y must have the same length")
    if bounds[0] <= 0 or bounds[1] <= bounds[0]:
        raise ValueError("bounds must define 0 < lower < upper")

    result = minimize_scalar(
        lambda temperature: _bce_with_logits(logits / temperature, labels),
        bounds=bounds,
        method="bounded",
    )
    if not result.success:
        raise RuntimeError(f"temperature fit failed: {result.message}")
    return float(result.x)


def apply_temperature(logits: np.ndarray, T: float) -> np.ndarray:
    """Apply T and return stable post-sigmoid Pneumonia=1 probabilities."""
    if T <= 0:
        raise ValueError("T must be > 0")
    z = np.asarray(logits, dtype=float) / float(T)
    return np.where(
        z >= 0,
        1.0 / (1.0 + np.exp(-z)),
        np.exp(z) / (1.0 + np.exp(z)),
    )


def evaluate_calibration(logits, y, T: float = 1.0, n_bins: int = 10) -> dict[str, float]:
    """Compute ECE/Brier and saturation diagnostics after applying T."""
    probabilities = apply_temperature(logits, T)
    labels = np.asarray(y, dtype=int)
    return {
        "ece_equal_width": ece(labels, probabilities, n_bins=n_bins, scheme="equal_width"),
        "ece_equal_mass": ece(labels, probabilities, n_bins=n_bins, scheme="equal_mass"),
        "brier": brier_score(labels, probabilities),
        "max_prob": float(probabilities.max()) if len(probabilities) else 0.0,
        "frac_prob_gt_099": float((probabilities > 0.99).mean()) if len(probabilities) else 0.0,
    }


def run_temperature_study(
    models: Sequence[str],
    val_dataset: str = "rsna_val",
    test_datasets: Sequence[str] | None = None,
    prediction_root: str | Path = "outputs/predictions",
    output_csv: str | Path = "outputs/temperature_scaling/ts_table.csv",
    n_bins: int = 10,
) -> list[dict[str, float | str]]:
    """Fit T on validation predictions and apply it to test predictions.

    This is deployable post-hoc calibration: T is never fit on a test set. The
    output reports calibration before and after T-scaling. AUC is asserted to be
    invariant because positive temperature scaling cannot alter score ranking.
    """
    if test_datasets is None:
        test_datasets = ["rsna", "kermany", "chittagong"]
    prediction_root = Path(prediction_root)
    rows = []

    for model in models:
        val_payload = load_npz_predictions(prediction_root / val_dataset / f"{model}.npz")
        temperature = fit_temperature(val_payload["y_logit"], val_payload["y_true"])

        for dataset in test_datasets:
            npz_path = prediction_root / dataset / f"{model}.npz"
            payload = load_npz_predictions(npz_path)
            logits = payload["y_logit"]
            labels = payload["y_true"]
            before = evaluate_calibration(logits, labels, T=1.0, n_bins=n_bins)
            after = evaluate_calibration(logits, labels, T=temperature, n_bins=n_bins)

            auc_before = roc_auc_score(labels, apply_temperature(logits, 1.0))
            auc_after = roc_auc_score(labels, apply_temperature(logits, temperature))
            if abs(auc_before - auc_after) >= 1e-9:
                raise AssertionError(
                    f"AUC changed after T-scaling ({model}, {dataset}): "
                    f"{auc_before} vs {auc_after}"
                )
            canonical_auc = metrics_from_npz(npz_path)["roc_auc"]

            rows.append(
                {
                    "model": model,
                    "dataset": dataset,
                    "T": temperature,
                    "ece_width_before": before["ece_equal_width"],
                    "ece_width_after": after["ece_equal_width"],
                    "ece_mass_before": before["ece_equal_mass"],
                    "ece_mass_after": after["ece_equal_mass"],
                    "ece_delta": after["ece_equal_mass"] - before["ece_equal_mass"],
                    "brier_before": before["brier"],
                    "brier_after": after["brier"],
                    "maxp_before": before["max_prob"],
                    "maxp_after": after["max_prob"],
                    "frac_prob_gt_099_before": before["frac_prob_gt_099"],
                    "frac_prob_gt_099_after": after["frac_prob_gt_099"],
                    "auc": canonical_auc,
                }
            )

    _write_csv(Path(output_csv), rows)
    return rows


def _write_csv(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    default_models = [
        "pneumonia_net",
        "resnet18",
        "mobilenet_v3_large",
        "efficientnet_b0",
        "densenet121",
    ]
    output_rows = run_temperature_study(default_models)
    for row in output_rows:
        print(
            f"{row['model']:<20} {row['dataset']:<10} T={float(row['T']):.4f} "
            f"ECE {float(row['ece_mass_before']):.3f}->{float(row['ece_mass_after']):.3f} "
            f"maxp {float(row['maxp_before']):.3f}->{float(row['maxp_after']):.3f}"
        )
