from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

import numpy as np

from thesis.metrics_canonical import load_npz_scores


FIELDNAMES = [
    "model",
    "dataset",
    "ece_equal_width",
    "ece_equal_mass",
    "brier_score",
]


def ece(
    y_true,
    y_score,
    n_bins: int = 10,
    scheme: str = "equal_width",
) -> float:
    """Compute Expected Calibration Error for Pneumonia=1 probabilities.

    y_score is already a post-sigmoid probability for the positive class
    Pneumonia=1; sigmoid must not be applied again.

    For bins B_m, ECE = sum_m |B_m| / N * |acc(B_m) - conf(B_m)|, where
    acc(B_m) is the fraction of positives in the bin and conf(B_m) is the
    mean predicted probability in the bin. equal_width uses fixed bins on
    [0, 1]. equal_mass sorts by score and splits samples into quantile bins,
    which is more informative when many scores saturate near 1.0.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    if y_true.shape[0] != y_score.shape[0]:
        raise ValueError("y_true and y_score must have the same length")
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")
    if len(y_true) == 0:
        return 0.0

    bins = _bin_indices(y_score, n_bins=n_bins, scheme=scheme)
    total = len(y_true)
    error = 0.0
    for indices in bins:
        if len(indices) == 0:
            continue
        accuracy = float(y_true[indices].mean())
        confidence = float(y_score[indices].mean())
        error += (len(indices) / total) * abs(accuracy - confidence)
    return float(error)


def brier_score(y_true, y_score) -> float:
    """Mean squared error between Pneumonia=1 labels and probabilities."""
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    if y_true.shape[0] != y_score.shape[0]:
        raise ValueError("y_true and y_score must have the same length")
    return float(np.mean((y_score - y_true) ** 2)) if len(y_true) else 0.0


def build_calibration_analysis(
    dataset_list: Sequence[str],
    model_list: Sequence[str],
    prediction_root: str | Path = "outputs/predictions",
    output_dir: str | Path = "outputs/calibration",
    n_bins: int = 10,
) -> list[dict[str, float | str]]:
    prediction_root = Path(prediction_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for model in model_list:
        for dataset in dataset_list:
            y_true, y_score = load_npz_scores(prediction_root / dataset / f"{model}.npz")
            rows.append(
                {
                    "model": model,
                    "dataset": dataset,
                    "ece_equal_width": ece(y_true, y_score, n_bins=n_bins, scheme="equal_width"),
                    "ece_equal_mass": ece(y_true, y_score, n_bins=n_bins, scheme="equal_mass"),
                    "brier_score": brier_score(y_true, y_score),
                }
            )

    _write_csv(output_dir / "ece_table.csv", rows)
    _write_difference_csv(output_dir / "ece_differences.csv", calibration_difference_rows(rows))
    _write_latex(output_dir / "ece_table.tex", rows)
    _write_report(output_dir / "interpretation.md", rows)
    for model in model_list:
        plot_reliability_diagram(
            model,
            dataset_list,
            prediction_root=prediction_root,
            output_path=output_dir / f"reliability_{model}.png",
            n_bins=n_bins,
        )
    return rows


def calibration_hypothesis_summary(rows: Sequence[dict]) -> dict[str, float | int | bool]:
    models = sorted({str(row["model"]) for row in rows})
    by_key = {(str(row["model"]), str(row["dataset"])): row for row in rows}
    ch_gt_rsna = 0
    ch_gt_kermany = 0
    diffs = []
    for model in models:
        ch = float(by_key[(model, "chittagong")]["ece_equal_mass"])
        rsna = float(by_key[(model, "rsna")]["ece_equal_mass"])
        kermany = float(by_key[(model, "kermany")]["ece_equal_mass"])
        diff_rsna = ch - rsna
        diff_kermany = ch - kermany
        diffs.append((diff_rsna, diff_kermany))
        ch_gt_rsna += int(diff_rsna > 0)
        ch_gt_kermany += int(diff_kermany > 0)
    majority = len(models) // 2 + 1
    return {
        "n_models": len(models),
        "chittagong_gt_rsna_count": ch_gt_rsna,
        "chittagong_gt_kermany_count": ch_gt_kermany,
        "majority_chittagong_higher_than_rsna": ch_gt_rsna >= majority,
        "majority_chittagong_higher_than_kermany": ch_gt_kermany >= majority,
        "mean_chittagong_minus_rsna": float(np.mean([item[0] for item in diffs])) if diffs else 0.0,
        "mean_chittagong_minus_kermany": float(np.mean([item[1] for item in diffs])) if diffs else 0.0,
    }


def calibration_difference_rows(rows: Sequence[dict]) -> list[dict[str, float | str | bool]]:
    models = sorted({str(row["model"]) for row in rows})
    by_key = {(str(row["model"]), str(row["dataset"])): row for row in rows}
    result = []
    for model in models:
        ch = float(by_key[(model, "chittagong")]["ece_equal_mass"])
        rsna = float(by_key[(model, "rsna")]["ece_equal_mass"])
        kermany = float(by_key[(model, "kermany")]["ece_equal_mass"])
        result.append(
            {
                "model": model,
                "ece_chittagong_minus_rsna": ch - rsna,
                "ece_chittagong_minus_kermany": ch - kermany,
                "chittagong_gt_rsna": ch > rsna,
                "chittagong_gt_kermany": ch > kermany,
            }
        )
    return result


def plot_reliability_diagram(
    model: str,
    dataset_list: Sequence[str],
    prediction_root: str | Path,
    output_path: str | Path,
    n_bins: int = 10,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    prediction_root = Path(prediction_root)
    fig, axis = plt.subplots(figsize=(6, 5))
    axis.plot([0, 1], [0, 1], linestyle="--", color="0.5", linewidth=1, label="perfect calibration")
    for dataset in dataset_list:
        y_true, y_score = load_npz_scores(prediction_root / dataset / f"{model}.npz")
        confidence, accuracy = reliability_points(y_true, y_score, n_bins=n_bins, scheme="equal_mass")
        axis.plot(confidence, accuracy, marker="o", label=dataset)
    axis.set_title(f"Reliability diagram: {model}")
    axis.set_xlabel("Mean predicted Pneumonia probability")
    axis.set_ylabel("Observed Pneumonia frequency")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.grid(True, alpha=0.25)
    axis.legend()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def reliability_points(
    y_true,
    y_score,
    n_bins: int = 10,
    scheme: str = "equal_mass",
) -> tuple[np.ndarray, np.ndarray]:
    y_true = np.asarray(y_true, dtype=int)
    y_score = np.asarray(y_score, dtype=float)
    bins = _bin_indices(y_score, n_bins=n_bins, scheme=scheme)
    confidence = []
    accuracy = []
    for indices in bins:
        if len(indices) == 0:
            continue
        confidence.append(float(y_score[indices].mean()))
        accuracy.append(float(y_true[indices].mean()))
    return np.asarray(confidence), np.asarray(accuracy)


def _bin_indices(y_score: np.ndarray, n_bins: int, scheme: str) -> list[np.ndarray]:
    if scheme == "equal_width":
        edges = np.linspace(0.0, 1.0, n_bins + 1)
        bins = []
        for index in range(n_bins):
            left = edges[index]
            right = edges[index + 1]
            if index == n_bins - 1:
                mask = (y_score >= left) & (y_score <= right)
            else:
                mask = (y_score >= left) & (y_score < right)
            bins.append(np.flatnonzero(mask))
        return bins
    if scheme == "equal_mass":
        order = np.argsort(y_score, kind="mergesort")
        return [np.asarray(chunk, dtype=int) for chunk in np.array_split(order, n_bins)]
    raise ValueError("scheme must be 'equal_width' or 'equal_mass'")


def _write_csv(path: Path, rows: Sequence[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _write_difference_csv(path: Path, rows: Sequence[dict]) -> None:
    with path.open("w", newline="") as handle:
        fieldnames = [
            "model",
            "ece_chittagong_minus_rsna",
            "ece_chittagong_minus_kermany",
            "chittagong_gt_rsna",
            "chittagong_gt_kermany",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_latex(path: Path, rows: Sequence[dict]) -> None:
    lines = [
        "\\begin{tabular}{llrrr}",
        "\\hline",
        "Model & Dataset & ECE width & ECE mass & Brier \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(
            f"{row['model']} & {row['dataset']} & "
            f"{float(row['ece_equal_width']):.3f} & "
            f"{float(row['ece_equal_mass']):.3f} & "
            f"{float(row['brier_score']):.3f} \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}", ""])
    path.write_text("\n".join(lines))


def _write_report(path: Path, rows: Sequence[dict]) -> None:
    summary = calibration_hypothesis_summary(rows)
    lines = [
        "# Calibration Analysis",
        "",
        "Scores are post-sigmoid Pneumonia=1 probabilities from canonical .npz files; sigmoid is not applied again.",
        "ECE is reported with equal-width bins on [0,1] and equal-mass quantile bins. Equal-mass is the primary diagnostic when scores saturate near 1.0, as in MobileNetV3 on RSNA.",
        "Brier score is included as a proper scoring-rule cross-check.",
        "",
        "## Chittagong Calibration Hypothesis",
        "",
        f"Models with ECE_mass(Chittagong) > ECE_mass(RSNA): {summary['chittagong_gt_rsna_count']}/{summary['n_models']}.",
        f"Models with ECE_mass(Chittagong) > ECE_mass(Kermany): {summary['chittagong_gt_kermany_count']}/{summary['n_models']}.",
        f"Mean ECE_mass Chittagong-RSNA: {summary['mean_chittagong_minus_rsna']:.4f}.",
        f"Mean ECE_mass Chittagong-Kermany: {summary['mean_chittagong_minus_kermany']:.4f}.",
        "",
    ]
    if summary["majority_chittagong_higher_than_rsna"] and summary["majority_chittagong_higher_than_kermany"]:
        lines.append("The calibration hypothesis is supported as a majority pattern: Chittagong ECE is higher for most models against both RSNA and Kermany, but it is not uniform across all architectures.")
    else:
        lines.append("The calibration story does not hold as a systematic explanation: Chittagong ECE is not higher for a majority of models against both RSNA and Kermany, so ranking instability likely has another cause or only partial calibration contribution.")
    lines.extend(["", "## Per-model ECE differences", ""])
    for row in calibration_difference_rows(rows):
        lines.append(
            f"- {row['model']}: Chittagong-RSNA={row['ece_chittagong_minus_rsna']:.4f}; "
            f"Chittagong-Kermany={row['ece_chittagong_minus_kermany']:.4f}."
        )
    mobile_rsna = next(
        (row for row in rows if row["model"] == "mobilenet_v3_large" and row["dataset"] == "rsna"),
        None,
    )
    if mobile_rsna is not None:
        lines.extend(
            [
                "",
                "## MobileNetV3 RSNA saturation check",
                "",
                "MobileNetV3 on RSNA contains many positive scores saturated near 1.0, but this does not by itself imply poor calibration: saturated positives are correct high-confidence predictions.",
                f"ECE width={float(mobile_rsna['ece_equal_width']):.4f}, ECE mass={float(mobile_rsna['ece_equal_mass']):.4f}, Brier={float(mobile_rsna['brier_score']):.4f}.",
            ]
        )
    path.write_text("\n".join(lines) + "\n")
