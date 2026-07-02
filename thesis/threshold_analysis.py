from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

import numpy as np
from sklearn.metrics import roc_curve

from thesis.metrics_canonical import metrics_from_npz, youden_threshold


ORACLE_NOTE = (
    "Youden oracle thresholds are selected on the same test dataset being reported. "
    "They are optimistic and non-deployable; this is a diagnostic analysis of "
    "discriminative power separated from the fixed operating point."
)
FIELDNAMES = [
    "dataset",
    "model",
    "rank_0_5",
    "rank_youden",
    "spearman_rank_correlation",
    "threshold_0_5",
    "youden_threshold",
    "balanced_accuracy_0_5",
    "balanced_accuracy_youden",
    "sensitivity_0_5",
    "sensitivity_youden",
    "specificity_0_5",
    "specificity_youden",
    "roc_auc",
    "pr_auc",
    "f1_0_5",
    "f1_youden",
]


def build_threshold_analysis(
    dataset_list: Sequence[str],
    model_list: Sequence[str],
    prediction_root: str | Path = "outputs/predictions",
    output_dir: str | Path = "outputs/threshold_analysis",
) -> list[dict[str, float | int | str | None]]:
    prediction_root = Path(prediction_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for dataset in dataset_list:
        for model in model_list:
            path = prediction_root / dataset / f"{model}.npz"
            fixed = metrics_from_npz(path, threshold=0.5)
            threshold = youden_threshold(path)
            calibrated = metrics_from_npz(path, threshold=threshold)
            rows.append(
                {
                    "dataset": dataset,
                    "model": model,
                    "threshold_0_5": 0.5,
                    "youden_threshold": threshold,
                    "balanced_accuracy_0_5": fixed["balanced_accuracy"],
                    "balanced_accuracy_youden": calibrated["balanced_accuracy"],
                    "sensitivity_0_5": fixed["sensitivity"],
                    "sensitivity_youden": calibrated["sensitivity"],
                    "specificity_0_5": fixed["specificity"],
                    "specificity_youden": calibrated["specificity"],
                    "roc_auc": fixed["roc_auc"],
                    "pr_auc": fixed["pr_auc"],
                    "f1_0_5": fixed["f1"],
                    "f1_youden": calibrated["f1"],
                }
            )

    _add_ranking_columns(rows)
    _write_csv(output_dir / "ranking_comparison.csv", rows)
    _write_gap_csv(output_dir / "external_gap_summary.csv", external_gap_summary(rows, model_list))
    _write_report(output_dir / "interpretation.md", rows)
    plot_roc_curves(dataset_list, model_list, prediction_root, output_dir / "roc_curves.png")
    return rows


def spearman_from_ranks(
    ranks_a: dict[str, int],
    ranks_b: dict[str, int],
) -> float:
    models = sorted(set(ranks_a) & set(ranks_b))
    n = len(models)
    if n < 2:
        return 1.0
    diffs = [(ranks_a[model] - ranks_b[model]) ** 2 for model in models]
    return float(1 - (6 * sum(diffs)) / (n * (n * n - 1)))


def densenet_focus(rows: Sequence[dict]) -> dict[str, float | bool]:
    by_dataset = {
        str(row["dataset"]): row
        for row in rows
        if row["model"] == "densenet121" and row["dataset"] in {"kermany", "chittagong"}
    }
    kermany = by_dataset["kermany"]
    chittagong = by_dataset["chittagong"]
    fixed_gap = float(kermany["balanced_accuracy_0_5"]) - float(
        chittagong["balanced_accuracy_0_5"]
    )
    youden_gap = float(kermany["balanced_accuracy_youden"]) - float(
        chittagong["balanced_accuracy_youden"]
    )
    return {
        "kermany_balanced_accuracy_0_5": float(kermany["balanced_accuracy_0_5"]),
        "kermany_balanced_accuracy_youden": float(kermany["balanced_accuracy_youden"]),
        "kermany_sensitivity_0_5": float(kermany["sensitivity_0_5"]),
        "kermany_specificity_0_5": float(kermany["specificity_0_5"]),
        "kermany_sensitivity_youden": float(kermany["sensitivity_youden"]),
        "kermany_specificity_youden": float(kermany["specificity_youden"]),
        "chittagong_balanced_accuracy_0_5": float(chittagong["balanced_accuracy_0_5"]),
        "chittagong_balanced_accuracy_youden": float(chittagong["balanced_accuracy_youden"]),
        "chittagong_sensitivity_0_5": float(chittagong["sensitivity_0_5"]),
        "chittagong_specificity_0_5": float(chittagong["specificity_0_5"]),
        "chittagong_sensitivity_youden": float(chittagong["sensitivity_youden"]),
        "chittagong_specificity_youden": float(chittagong["specificity_youden"]),
        "fixed_gap_kermany_minus_chittagong": fixed_gap,
        "youden_gap_kermany_minus_chittagong": youden_gap,
        "gap_reduced": abs(youden_gap) < abs(fixed_gap),
        "gap_substantially_reduced": abs(youden_gap) <= 0.5 * abs(fixed_gap),
    }


def external_gap_summary(
    rows: Sequence[dict],
    model_list: Sequence[str],
) -> list[dict[str, float | str]]:
    by_key = {(str(row["dataset"]), str(row["model"])): row for row in rows}
    summary = []
    for model in model_list:
        kermany = by_key[("kermany", model)]
        chittagong = by_key[("chittagong", model)]
        gap_ba = float(kermany["balanced_accuracy_youden"]) - float(
            chittagong["balanced_accuracy_youden"]
        )
        gap_auc = float(kermany["roc_auc"]) - float(chittagong["roc_auc"])
        summary.append(
            {
                "model": model,
                "gap_ba_youden": gap_ba,
                "gap_auc": gap_auc,
                "gap_difference": gap_ba - gap_auc,
            }
        )
    return summary


def plot_roc_curves(
    dataset_list: Sequence[str],
    model_list: Sequence[str],
    prediction_root: str | Path,
    output_path: str | Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    prediction_root = Path(prediction_root)
    fig, axes = plt.subplots(1, len(dataset_list), figsize=(6 * len(dataset_list), 5), squeeze=False)
    axes = axes[0]
    for axis, dataset in zip(axes, dataset_list):
        for model in model_list:
            path = prediction_root / dataset / f"{model}.npz"
            y_true, y_score = _load_npz_arrays(path)
            fpr, tpr, _ = roc_curve(y_true, y_score)
            auc = metrics_from_npz(path)["roc_auc"]
            axis.plot(fpr, tpr, label=f"{model} (AUC={auc:.3f})")

            fixed = metrics_from_npz(path, threshold=0.5)
            oracle_threshold = youden_threshold(path)
            oracle = metrics_from_npz(path, threshold=oracle_threshold)
            axis.scatter(
                1 - float(fixed["specificity"]),
                float(fixed["sensitivity"]),
                marker="o",
                s=28,
            )
            axis.scatter(
                1 - float(oracle["specificity"]),
                float(oracle["sensitivity"]),
                marker="x",
                s=42,
            )

        axis.plot([0, 1], [0, 1], linestyle="--", color="0.6", linewidth=1)
        axis.set_title(dataset)
        axis.set_xlabel("False positive rate")
        axis.set_ylabel("True positive rate")
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
        axis.grid(True, alpha=0.25)
        axis.legend(fontsize=8)
    fig.suptitle("ROC curves with fixed 0.5 points (circles) and Youden oracle points (x)")
    fig.tight_layout()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def _add_ranking_columns(rows: list[dict]) -> None:
    for dataset in sorted({row["dataset"] for row in rows}):
        dataset_rows = [row for row in rows if row["dataset"] == dataset]
        fixed_ranks = _rank_rows(dataset_rows, "balanced_accuracy_0_5")
        youden_ranks = _rank_rows(dataset_rows, "balanced_accuracy_youden")
        spearman = spearman_from_ranks(fixed_ranks, youden_ranks)
        for row in dataset_rows:
            model = str(row["model"])
            row["rank_0_5"] = fixed_ranks[model]
            row["rank_youden"] = youden_ranks[model]
            row["spearman_rank_correlation"] = spearman


def _rank_rows(rows: Sequence[dict], metric: str) -> dict[str, int]:
    ordered = sorted(rows, key=lambda row: (-float(row[metric]), str(row["model"])))
    return {str(row["model"]): rank for rank, row in enumerate(ordered, start=1)}


def _write_csv(path: Path, rows: Sequence[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_gap_csv(path: Path, rows: Sequence[dict]) -> None:
    with path.open("w", newline="") as handle:
        fieldnames = ["model", "gap_ba_youden", "gap_auc", "gap_difference"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_report(path: Path, rows: Sequence[dict]) -> None:
    lines = [
        "# Threshold Analysis",
        "",
        ORACLE_NOTE,
        "",
        "Interpretation rule: if the ranking at Youden oracle collapses "
        "(low Spearman or models clustered within noise) while AUC ordering differs, "
        "the fixed 0.5 threshold is measuring the operating point rather than architecture. "
        "If ranking remains stable at Youden, the threshold-effect hypothesis is falsified "
        "or only partially supported.",
        "",
        "## Dataset Ranking",
    ]
    for dataset in sorted({row["dataset"] for row in rows}):
        dataset_rows = [row for row in rows if row["dataset"] == dataset]
        spearman = dataset_rows[0]["spearman_rank_correlation"]
        lines.extend(["", f"### {dataset}", "", f"Spearman rank correlation: {spearman:.3f}", ""])
        for row in sorted(dataset_rows, key=lambda item: int(item["rank_0_5"])):
            lines.append(
                f"- {row['model']}: rank@0.5={row['rank_0_5']}, "
                f"rank@Youden={row['rank_youden']}, "
                f"BA@0.5={row['balanced_accuracy_0_5']:.3f}, "
                f"BA@Youden={row['balanced_accuracy_youden']:.3f}, "
                f"AUC={row['roc_auc']:.3f}"
            )

    if {"kermany", "chittagong"}.issubset({row["dataset"] for row in rows}):
        focus = densenet_focus(rows)
        lines.extend(
            [
                "",
                "## DenseNet121 Focus",
                "",
                f"Kermany BA: 0.5={focus['kermany_balanced_accuracy_0_5']:.3f}, "
                f"Youden={focus['kermany_balanced_accuracy_youden']:.3f}.",
                f"Chittagong BA: 0.5={focus['chittagong_balanced_accuracy_0_5']:.3f}, "
                f"Youden={focus['chittagong_balanced_accuracy_youden']:.3f}.",
                f"Gap Kermany-Chittagong: 0.5={focus['fixed_gap_kermany_minus_chittagong']:.3f}, "
                f"Youden={focus['youden_gap_kermany_minus_chittagong']:.3f}.",
            ]
        )
        if focus["gap_substantially_reduced"]:
            lines.append("The DenseNet121 gap substantially shrinks after oracle threshold calibration.")
        elif focus["gap_reduced"]:
            lines.append(
                "The DenseNet121 gap shrinks only marginally after oracle threshold calibration; "
                "the Kermany-vs-Chittagong difference remains mostly intact."
            )
        else:
            lines.append("The DenseNet121 gap does not shrink after oracle threshold calibration.")
    path.write_text("\n".join(lines) + "\n")


def _load_npz_arrays(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    with np.load(path, allow_pickle=False) as payload:
        return (
            np.asarray(payload["y_true"], dtype=int),
            np.asarray(payload["y_score"], dtype=float),
        )
