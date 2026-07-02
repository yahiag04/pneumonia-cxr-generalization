import tempfile
import unittest
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from thesis.temperature_scaling import (
    _bce_with_logits,
    apply_temperature,
    evaluate_calibration,
    fit_temperature,
    run_temperature_study,
)


class TemperatureScalingTest(unittest.TestCase):
    def test_bce_with_logits_is_stable_for_large_logits(self):
        logits = np.array([-1000.0, 1000.0])
        labels = np.array([0, 1])

        loss = _bce_with_logits(logits, labels)

        self.assertTrue(np.isfinite(loss))
        self.assertLess(loss, 1e-6)

    def test_apply_temperature_returns_monotonic_probabilities(self):
        logits = np.array([-4.0, 0.0, 4.0])

        probabilities = apply_temperature(logits, T=2.0)

        self.assertTrue(np.all(np.diff(probabilities) > 0))
        self.assertAlmostEqual(probabilities[1], 0.5)
        self.assertGreater(probabilities[0], 0.0)
        self.assertLess(probabilities[-1], 1.0)

    def test_fit_temperature_returns_positive_temperature(self):
        logits = np.array([-5.0, -3.0, 3.0, 5.0])
        labels = np.array([0, 0, 1, 1])

        temperature = fit_temperature(logits, labels)

        self.assertGreater(temperature, 0.0)

    def test_temperature_scaling_preserves_auc(self):
        logits = np.array([-2.0, 0.2, 1.0, 3.0, -1.0])
        labels = np.array([0, 0, 1, 1, 0])

        before = roc_auc_score(labels, apply_temperature(logits, T=1.0))
        after = roc_auc_score(labels, apply_temperature(logits, T=3.0))

        self.assertEqual(before, after)

    def test_evaluate_calibration_reports_ece_brier_and_saturation(self):
        logits = np.array([-4.0, 0.0, 4.0])
        labels = np.array([0, 1, 1])

        result = evaluate_calibration(logits, labels, T=1.0, n_bins=2)

        self.assertIn("ece_equal_width", result)
        self.assertIn("ece_equal_mass", result)
        self.assertIn("brier", result)
        self.assertIn("max_prob", result)
        self.assertIn("frac_prob_gt_099", result)

    def test_run_temperature_study_reads_validation_logits_and_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_prediction_npz(root / "predictions" / "rsna_val" / "model_a.npz")
            self.write_prediction_npz(root / "predictions" / "rsna" / "model_a.npz")
            output_csv = root / "temperature" / "ts_table.csv"

            rows = run_temperature_study(
                ["model_a"],
                val_dataset="rsna_val",
                test_datasets=["rsna"],
                prediction_root=root / "predictions",
                output_csv=output_csv,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["model"], "model_a")
            self.assertEqual(rows[0]["dataset"], "rsna")
            self.assertGreater(rows[0]["T"], 0.0)
            self.assertTrue(output_csv.exists())

    @staticmethod
    def write_prediction_npz(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        logits = np.array([-3.0, -1.0, 1.0, 3.0])
        labels = np.array([0, 0, 1, 1])
        probabilities = apply_temperature(logits, T=1.0)
        np.savez_compressed(
            path,
            y_true=labels,
            y_score=probabilities,
            y_logit=logits,
            sample_id=np.array(["a", "b", "c", "d"], dtype=str),
        )


if __name__ == "__main__":
    unittest.main()
