import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from thesis.threshold_analysis import (
    build_threshold_analysis,
    densenet_focus,
    external_gap_summary,
    spearman_from_ranks,
)


class ThresholdAnalysisTest(unittest.TestCase):
    def write_npz(self, path: Path, labels, scores) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            y_true=np.asarray(labels, dtype=int),
            y_score=np.asarray(scores, dtype=float),
            sample_id=np.asarray([f"s{i}" for i in range(len(labels))], dtype=str),
        )

    def test_spearman_from_ranks_is_exact_for_identical_and_reversed(self):
        self.assertEqual(spearman_from_ranks({"a": 1, "b": 2}, {"a": 1, "b": 2}), 1.0)
        self.assertEqual(spearman_from_ranks({"a": 1, "b": 2}, {"a": 2, "b": 1}), -1.0)

    def test_build_threshold_analysis_writes_csv_report_and_plot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            datasets = ["kermany", "chittagong"]
            models = ["densenet121", "resnet18"]
            for dataset in datasets:
                self.write_npz(
                    root / "predictions" / dataset / "densenet121.npz",
                    [0, 0, 1, 1],
                    [0.1, 0.8, 0.9, 0.4],
                )
                self.write_npz(
                    root / "predictions" / dataset / "resnet18.npz",
                    [0, 0, 1, 1],
                    [0.1, 0.2, 0.8, 0.9],
                )

            rows = build_threshold_analysis(
                datasets,
                models,
                prediction_root=root / "predictions",
                output_dir=root / "threshold_analysis",
            )

            csv_path = root / "threshold_analysis" / "ranking_comparison.csv"
            report_path = root / "threshold_analysis" / "interpretation.md"
            plot_path = root / "threshold_analysis" / "roc_curves.png"
            self.assertTrue(csv_path.exists())
            self.assertTrue(report_path.exists())
            self.assertTrue(plot_path.exists())
            self.assertEqual(len(rows), 4)
            with csv_path.open() as handle:
                csv_rows = list(csv.DictReader(handle))
            self.assertIn("spearman_rank_correlation", csv_rows[0])
            self.assertIn("Youden oracle", report_path.read_text())

    def test_densenet_focus_reports_gap_change(self):
        rows = [
            {
                "dataset": "kermany",
                "model": "densenet121",
                "balanced_accuracy_0_5": 0.86,
                "balanced_accuracy_youden": 0.87,
                "sensitivity_0_5": 0.85,
                "specificity_0_5": 0.87,
                "sensitivity_youden": 0.86,
                "specificity_youden": 0.88,
            },
            {
                "dataset": "chittagong",
                "model": "densenet121",
                "balanced_accuracy_0_5": 0.76,
                "balanced_accuracy_youden": 0.85,
                "sensitivity_0_5": 0.60,
                "specificity_0_5": 0.92,
                "sensitivity_youden": 0.84,
                "specificity_youden": 0.86,
            },
        ]

        focus = densenet_focus(rows)

        self.assertAlmostEqual(focus["fixed_gap_kermany_minus_chittagong"], 0.10)
        self.assertAlmostEqual(focus["youden_gap_kermany_minus_chittagong"], 0.02)
        self.assertTrue(focus["gap_reduced"])
        self.assertTrue(focus["gap_substantially_reduced"])

    def test_external_gap_summary_compares_youden_ba_and_auc_gaps(self):
        rows = [
            {
                "dataset": "kermany",
                "model": "densenet121",
                "balanced_accuracy_youden": 0.863,
                "roc_auc": 0.925,
            },
            {
                "dataset": "chittagong",
                "model": "densenet121",
                "balanced_accuracy_youden": 0.776,
                "roc_auc": 0.844,
            },
        ]

        summary = external_gap_summary(rows, ["densenet121"])

        self.assertEqual(summary[0]["model"], "densenet121")
        self.assertAlmostEqual(summary[0]["gap_ba_youden"], 0.087)
        self.assertAlmostEqual(summary[0]["gap_auc"], 0.081)
        self.assertAlmostEqual(summary[0]["gap_difference"], 0.006)


if __name__ == "__main__":
    unittest.main()
