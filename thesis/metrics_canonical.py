from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Sequence

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve


TABLE_FIELDS = [
    "dataset",
    "model",
    "rank",
    "youden_rank",
    "n",
    "n_pos",
    "n_neg",
    "threshold",
    "tp",
    "fp",
    "tn",
    "fn",
    "sensitivity",
    "specificity",
    "balanced_accuracy",
    "roc_auc",
    "pr_auc",
    "f1",
    "youden_threshold",
    "youden_tp",
    "youden_fp",
    "youden_tn",
    "youden_fn",
    "youden_sensitivity",
    "youden_specificity",
    "youden_balanced_accuracy",
    "youden_f1",
]
LEGACY_METRICS = [
    "sensitivity",
    "specificity",
    "balanced_accuracy",
    "roc_auc",
    "pr_auc",
    "f1",
]


def metrics_from_npz(path: str | Path, threshold: float = 0.5) -> dict[str, float | int | None]:
    """Compute canonical binary metrics from saved per-sample scores.

    The positive class is Pneumonia=1. Therefore sensitivity, PR-AUC, and F1
    are computed for the pneumonia class. Metrics are always recomputed from
    y_true/y_score in the .npz file; aggregate JSON files are not read.
    """
    y_true, y_score = _load_npz_arrays(path)
    y_pred = (y_score >= threshold).astype(int)

    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tp = int(((y_true == 1) & (y_pred == 1)).sum())

    sensitivity = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    precision = _safe_div(tp, tp + fp)
    f1 = _safe_div(2 * precision * sensitivity, precision + sensitivity)

    return {
        "n": int(len(y_true)),
        "n_pos": int((y_true == 1).sum()),
        "n_neg": int((y_true == 0).sum()),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balanced_accuracy": (sensitivity + specificity) / 2,
        "roc_auc": _auc_or_none(y_true, y_score),
        "pr_auc": _pr_auc_or_none(y_true, y_score),
        "f1": f1,
        "threshold": float(threshold),
    }


def load_npz_scores(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load canonical y_true/y_score arrays from a prediction .npz file."""
    return _load_npz_arrays(path)


def load_npz_predictions(path: str | Path) -> dict[str, np.ndarray]:
    """Load canonical per-sample prediction arrays, including pre-sigmoid logits.

    The positive class is Pneumonia=1. y_score is the post-sigmoid probability
    for Pneumonia=1; y_logit is the corresponding pre-sigmoid logit saved at
    inference time and must not be reconstructed from y_score.
    """
    path = Path(path)
    with np.load(path, allow_pickle=False) as payload:
        y_true = np.asarray(payload["y_true"], dtype=int)
        y_score = np.asarray(payload["y_score"], dtype=float)
        y_logit = np.asarray(payload["y_logit"], dtype=float)
        sample_id = np.asarray(payload["sample_id"], dtype=str)
    lengths = {len(y_true), len(y_score), len(y_logit), len(sample_id)}
    if len(lengths) != 1:
        raise ValueError(f"Prediction array length mismatch in {path}")
    return {
        "y_true": y_true,
        "y_score": y_score,
        "y_logit": y_logit,
        "sample_id": sample_id,
    }


def youden_threshold(path: str | Path) -> float:
    """Return the threshold maximizing Youden's J = sensitivity + specificity - 1."""
    y_true, y_score = _load_npz_arrays(path)
    if len(set(y_true.tolist())) < 2:
        return 0.5
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    finite = np.isfinite(thresholds)
    if not finite.any():
        return 0.5
    j_scores = tpr[finite] - fpr[finite]
    finite_thresholds = thresholds[finite]
    best_index = int(np.argmax(j_scores))
    return float(finite_thresholds[best_index])


def build_table(
    dataset_list: Sequence[str],
    model_list: Sequence[str],
    prediction_root: str | Path = "outputs/predictions",
    output_csv: str | Path = "outputs/canonical_metrics/table7_canonical.csv",
    output_latex: str | Path = "outputs/canonical_metrics/table7_canonical.tex",
) -> list[dict[str, float | int | str | None]]:
    rows = []
    prediction_root = Path(prediction_root)
    for dataset in dataset_list:
        for model in model_list:
            npz_path = prediction_root / dataset / f"{model}.npz"
            fixed = metrics_from_npz(npz_path, threshold=0.5)
            threshold = youden_threshold(npz_path)
            calibrated = metrics_from_npz(npz_path, threshold=threshold)
            row = {"dataset": dataset, "model": model, **fixed}
            row.update(
                {
                    "youden_threshold": threshold,
                    "youden_tp": calibrated["tp"],
                    "youden_fp": calibrated["fp"],
                    "youden_tn": calibrated["tn"],
                    "youden_fn": calibrated["fn"],
                    "youden_sensitivity": calibrated["sensitivity"],
                    "youden_specificity": calibrated["specificity"],
                    "youden_balanced_accuracy": calibrated["balanced_accuracy"],
                    "youden_f1": calibrated["f1"],
                }
            )
            rows.append(row)

    _add_ranks(rows)
    _write_csv(Path(output_csv), rows)
    _write_latex(Path(output_latex), rows)
    return rows


def compare_legacy_json(
    prediction_npz: str | Path,
    legacy_json: str | Path,
    warn_threshold: float = 1e-3,
) -> list[dict[str, float | str | bool | None]]:
    canonical = metrics_from_npz(prediction_npz, threshold=0.5)
    legacy = json.loads(Path(legacy_json).read_text())
    if "test_metrics" in legacy:
        legacy = legacy["test_metrics"]

    rows = []
    for metric in LEGACY_METRICS:
        legacy_key = "f1_pneumonia" if metric == "f1" else metric
        canonical_value = canonical.get(metric)
        legacy_value = legacy.get(legacy_key)
        delta = None
        large_difference = False
        if canonical_value is not None and legacy_value is not None:
            delta = float(canonical_value) - float(legacy_value)
            large_difference = abs(delta) - warn_threshold > 1e-12
        rows.append(
            {
                "metric": metric,
                "canonical": canonical_value,
                "legacy": legacy_value,
                "delta": delta,
                "large_difference": large_difference,
            }
        )
    return rows


def print_legacy_comparison(rows: Sequence[dict]) -> None:
    print("metric,canonical,legacy,delta,flag")
    for row in rows:
        flag = "INVESTIGATE" if row["large_difference"] else ""
        print(
            f"{row['metric']},{row['canonical']},{row['legacy']},"
            f"{row['delta']},{flag}"
        )


def _load_npz_arrays(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    with np.load(path, allow_pickle=False) as payload:
        y_true = np.asarray(payload["y_true"], dtype=int)
        y_score = np.asarray(payload["y_score"], dtype=float)
    if y_true.shape[0] != y_score.shape[0]:
        raise ValueError(f"y_true/y_score length mismatch in {path}")
    return y_true, y_score


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def _auc_or_none(y_true: np.ndarray, y_score: np.ndarray) -> float | None:
    if len(set(y_true.tolist())) < 2:
        return None
    return float(roc_auc_score(y_true, y_score))


def _pr_auc_or_none(y_true: np.ndarray, y_score: np.ndarray) -> float | None:
    if len(set(y_true.tolist())) < 2:
        return None
    return float(average_precision_score(y_true, y_score))


def _write_csv(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TABLE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _add_ranks(rows: list[dict]) -> None:
    datasets = sorted({row["dataset"] for row in rows})
    for dataset in datasets:
        dataset_rows = [row for row in rows if row["dataset"] == dataset]
        fixed_order = sorted(
            dataset_rows,
            key=lambda row: (-float(row["balanced_accuracy"]), str(row["model"])),
        )
        youden_order = sorted(
            dataset_rows,
            key=lambda row: (-float(row["youden_balanced_accuracy"]), str(row["model"])),
        )
        for rank, row in enumerate(fixed_order, start=1):
            row["rank"] = rank
        for rank, row in enumerate(youden_order, start=1):
            row["youden_rank"] = rank


def _write_latex(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{tabular}{llrrrrrrrr}",
        "\\hline",
        "Dataset & Model & BA@0.5 & Sens@0.5 & Spec@0.5 & AUC & PR-AUC & F1@0.5 & Youden $t$ & BA@Youden \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(
            f"{row['dataset']} & {row['model']} & "
            f"{_fmt(row['balanced_accuracy'])} & {_fmt(row['sensitivity'])} & "
            f"{_fmt(row['specificity'])} & {_fmt(row['roc_auc'])} & "
            f"{_fmt(row['pr_auc'])} & {_fmt(row['f1'])} & "
            f"{_fmt(row['youden_threshold'])} & {_fmt(row['youden_balanced_accuracy'])} \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}", ""])
    path.write_text("\n".join(lines))


def _fmt(value) -> str:
    if value is None:
        return "--"
    return f"{float(value):.3f}"
