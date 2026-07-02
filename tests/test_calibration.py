import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from thesis.calibration import (
    brier_score,
    build_calibration_analysis,
    calibration_hypothesis_summary,
    ece,
)


class CalibrationTest(unittest.TestCase):
    def write_npz(self, path: Path, labels, scores) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            y_true=np.asarray(labels, dtype=int),
            y_score=np.asarray(scores, dtype=float),
            sample_id=np.asarray([f"s{i}" for i in range(len(labels))], dtype=str),
        )

    def test_ece_equal_width_matches_explicit_bin_formula(self):
        y_true = np.array([0, 1, 1, 0])
        y_score = np.array([0.1, 0.2, 0.8, 0.9])

        value = ece(y_true, y_score, n_bins=2, scheme="equal_width")

        self.assertAlmostEqual(value, 0.35)

    def test_ece_equal_mass_uses_sorted_quantile_chunks(self):
        y_true = np.array([0, 1, 1, 0])
        y_score = np.array([0.1, 0.2, 0.8, 0.9])

        value = ece(y_true, y_score, n_bins=2, scheme="equal_mass")

        self.assertAlmostEqual(value, 0.35)

    def test_brier_score(self):
        y_true = np.array([0, 1])
        y_score = np.array([0.25, 0.75])

        self.assertAlmostEqual(brier_score(y_true, y_score), 0.0625)

    def test_build_calibration_analysis_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for dataset, scores in {
                "rsna": [0.1, 0.2, 0.8, 0.9],
                "kermany": [0.1, 0.4, 0.6, 0.9],
                "chittagong": [0.4, 0.6, 0.6, 0.8],
            }.items():
                self.write_npz(root / "predictions" / dataset / "model_a.npz", [0, 0, 1, 1], scores)

            rows = build_calibration_analysis(
                ["rsna", "kermany", "chittagong"],
                ["model_a"],
                prediction_root=root / "predictions",
                output_dir=root / "calibration",
                n_bins=2,
            )

            csv_path = root / "calibration" / "ece_table.csv"
            diff_path = root / "calibration" / "ece_differences.csv"
            latex_path = root / "calibration" / "ece_table.tex"
            report_path = root / "calibration" / "interpretation.md"
            plot_path = root / "calibration" / "reliability_model_a.png"
            self.assertEqual(len(rows), 3)
            self.assertTrue(csv_path.exists())
            self.assertTrue(diff_path.exists())
            self.assertTrue(latex_path.exists())
            self.assertTrue(report_path.exists())
            self.assertTrue(plot_path.exists())
            with csv_path.open() as handle:
                csv_rows = list(csv.DictReader(handle))
            self.assertIn("ece_equal_width", csv_rows[0])
            self.assertIn("ece_equal_mass", csv_rows[0])
            self.assertIn("brier_score", csv_rows[0])

    def test_calibration_hypothesis_summary_counts_majority(self):
        rows = [
            {"model": "a", "dataset": "rsna", "ece_equal_mass": 0.1},
            {"model": "a", "dataset": "kermany", "ece_equal_mass": 0.2},
            {"model": "a", "dataset": "chittagong", "ece_equal_mass": 0.3},
            {"model": "b", "dataset": "rsna", "ece_equal_mass": 0.1},
            {"model": "b", "dataset": "kermany", "ece_equal_mass": 0.2},
            {"model": "b", "dataset": "chittagong", "ece_equal_mass": 0.05},
            {"model": "c", "dataset": "rsna", "ece_equal_mass": 0.1},
            {"model": "c", "dataset": "kermany", "ece_equal_mass": 0.2},
            {"model": "c", "dataset": "chittagong", "ece_equal_mass": 0.4},
        ]

        summary = calibration_hypothesis_summary(rows)

        self.assertEqual(summary["chittagong_gt_rsna_count"], 2)
        self.assertEqual(summary["chittagong_gt_kermany_count"], 2)
        self.assertTrue(summary["majority_chittagong_higher_than_rsna"])
        self.assertTrue(summary["majority_chittagong_higher_than_kermany"])


if __name__ == "__main__":
    unittest.main()
