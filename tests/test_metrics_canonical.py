import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from thesis.metrics_canonical import (
    build_table,
    compare_legacy_json,
    load_npz_predictions,
    metrics_from_npz,
    youden_threshold,
)


class CanonicalMetricsTest(unittest.TestCase):
    def write_npz(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            y_true=np.array([0, 0, 1, 1]),
            y_score=np.array([0.1, 0.8, 0.9, 0.4]),
            y_logit=np.array([-2.19722458, 1.38629436, 2.19722458, -0.40546511]),
            sample_id=np.array(["a", "b", "c", "d"], dtype=str),
        )

    def test_metrics_from_npz_uses_positive_pneumonia_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            npz_path = Path(tmp) / "predictions.npz"
            self.write_npz(npz_path)

            metrics = metrics_from_npz(npz_path)

        self.assertEqual(metrics["n"], 4)
        self.assertEqual(metrics["n_pos"], 2)
        self.assertEqual(metrics["n_neg"], 2)
        self.assertEqual(metrics["tp"], 1)
        self.assertEqual(metrics["fp"], 1)
        self.assertEqual(metrics["tn"], 1)
        self.assertEqual(metrics["fn"], 1)
        self.assertAlmostEqual(metrics["sensitivity"], 0.5)
        self.assertAlmostEqual(metrics["specificity"], 0.5)
        self.assertAlmostEqual(metrics["balanced_accuracy"], 0.5)
        self.assertAlmostEqual(metrics["roc_auc"], 0.75)
        self.assertAlmostEqual(metrics["pr_auc"], 5 / 6)
        self.assertAlmostEqual(metrics["f1"], 0.5)

    def test_load_npz_predictions_exposes_logits_without_recomputing_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            npz_path = Path(tmp) / "predictions.npz"
            self.write_npz(npz_path)

            payload = load_npz_predictions(npz_path)

        np.testing.assert_array_equal(payload["y_true"], np.array([0, 0, 1, 1]))
        np.testing.assert_allclose(payload["y_score"], np.array([0.1, 0.8, 0.9, 0.4]))
        np.testing.assert_allclose(
            payload["y_logit"],
            np.array([-2.19722458, 1.38629436, 2.19722458, -0.40546511]),
        )

    def test_youden_threshold_selects_threshold_that_maximizes_j(self):
        with tempfile.TemporaryDirectory() as tmp:
            npz_path = Path(tmp) / "predictions.npz"
            self.write_npz(npz_path)

            threshold = youden_threshold(npz_path)
            metrics = metrics_from_npz(npz_path, threshold=threshold)

        self.assertAlmostEqual(threshold, 0.9)
        self.assertAlmostEqual(metrics["sensitivity"], 0.5)
        self.assertAlmostEqual(metrics["specificity"], 1.0)
        self.assertAlmostEqual(metrics["balanced_accuracy"], 0.75)

    def test_metrics_from_npz_is_exactly_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            npz_path = Path(tmp) / "predictions.npz"
            self.write_npz(npz_path)

            first = metrics_from_npz(npz_path)
            second = metrics_from_npz(npz_path)

        for key in first:
            self.assertEqual(first[key], second[key], key)

    def test_build_table_writes_csv_and_latex_from_npz_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for dataset in ["rsna", "kermany"]:
                for model in ["a", "b"]:
                    self.write_npz(root / "predictions" / dataset / f"{model}.npz")
            csv_path = root / "canonical.csv"
            latex_path = root / "canonical.tex"

            rows = build_table(
                ["rsna", "kermany"],
                ["a", "b"],
                prediction_root=root / "predictions",
                output_csv=csv_path,
                output_latex=latex_path,
            )

            self.assertEqual(len(rows), 4)
            self.assertTrue(csv_path.exists())
            self.assertTrue(latex_path.exists())
            self.assertIn("dataset,model,rank,youden_rank,n,n_pos,n_neg", csv_path.read_text())
            self.assertIn("\\begin{tabular}", latex_path.read_text())
            self.assertIn("youden_threshold", rows[0])
            self.assertIn("youden_balanced_accuracy", rows[0])
            self.assertIn("rank", rows[0])
            self.assertIn("youden_rank", rows[0])

    def test_compare_legacy_json_reports_differences_without_asserting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            npz_path = root / "predictions.npz"
            json_path = root / "legacy.json"
            self.write_npz(npz_path)
            json_path.write_text(
                json.dumps(
                    {
                        "sensitivity": 0.5,
                        "specificity": 0.5,
                        "balanced_accuracy": 0.501,
                        "roc_auc": 0.75,
                        "pr_auc": 0.8,
                    }
                )
            )

            rows = compare_legacy_json(npz_path, json_path, warn_threshold=1e-3)

        by_metric = {row["metric"]: row for row in rows}
        self.assertAlmostEqual(by_metric["balanced_accuracy"]["delta"], -0.001)
        self.assertFalse(by_metric["balanced_accuracy"]["large_difference"])
        self.assertTrue(by_metric["pr_auc"]["large_difference"])


if __name__ == "__main__":
    unittest.main()
