import unittest
import tempfile
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from PIL import Image

from thesis.model_registry import build_model
from thesis.predictions import verify_prediction_metrics
from thesis.train import collect_predictions, evaluate_checkpoint, evaluate_loader, keep_frozen_modules_eval


class IdentityLogitModel(nn.Module):
    def forward(self, x):
        return x[:, :1]


class PredictionCollectionTest(unittest.TestCase):
    def test_collect_predictions_returns_reusable_probabilities_and_loss(self):
        inputs = torch.tensor([[-2.0], [0.0], [2.0]])
        labels = torch.tensor([0, 1, 1])
        loader = DataLoader(TensorDataset(inputs, labels), batch_size=2)
        criterion = nn.BCEWithLogitsLoss()

        result = collect_predictions(
            IdentityLogitModel(),
            loader,
            criterion,
            torch.device("cpu"),
        )

        expected_probabilities = torch.sigmoid(inputs.squeeze(1)).tolist()
        expected_logits = inputs.squeeze(1).tolist()
        expected_loss = criterion(inputs.squeeze(1), labels.float()).item()
        self.assertEqual(result["labels"], labels.tolist())
        self.assertEqual(result["logits"], expected_logits)
        self.assertEqual(result["num_samples"], 3)
        self.assertAlmostEqual(result["loss"], expected_loss)
        for actual, expected in zip(result["probabilities"], expected_probabilities):
            self.assertAlmostEqual(actual, expected)
        self.assertGreaterEqual(result["elapsed_seconds"], 0.0)


class PredictionPersistenceTest(unittest.TestCase):
    def test_evaluate_loader_persists_per_sample_scores(self):
        inputs = torch.tensor([[-2.0], [0.0], [2.0]])
        labels = torch.tensor([0, 1, 1])
        loader = DataLoader(TensorDataset(inputs, labels), batch_size=2)
        criterion = nn.BCEWithLogitsLoss()

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "predictions.npz"
            metrics = evaluate_loader(
                IdentityLogitModel(),
                loader,
                criterion,
                torch.device("cpu"),
                prediction_output_path=output_path,
                sample_ids=["sample-0", "sample-1", "sample-2"],
            )
            payload = np.load(output_path)

        self.assertEqual(payload["y_true"].tolist(), labels.tolist())
        np.testing.assert_allclose(payload["y_logit"], inputs.squeeze(1).numpy())
        expected_probabilities = torch.sigmoid(inputs.squeeze(1)).numpy()
        np.testing.assert_allclose(payload["y_score"], expected_probabilities)
        self.assertEqual(payload["sample_id"].tolist(), ["sample-0", "sample-1", "sample-2"])
        self.assertAlmostEqual(metrics["balanced_accuracy"], 1.0)

    def test_verify_prediction_metrics_matches_aggregate_json(self):
        labels = np.array([0, 0, 1, 1])
        scores = np.array([0.1, 0.8, 0.9, 0.4])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            npz_path = root / "predictions.npz"
            json_path = root / "aggregate.json"
            np.savez_compressed(
                npz_path,
                y_true=labels,
                y_score=scores,
                sample_id=np.array(["a", "b", "c", "d"], dtype=str),
            )
            json_path.write_text(
                json.dumps(
                    {
                        "sensitivity": 0.5,
                        "specificity": 0.5,
                        "balanced_accuracy": 0.5,
                        "roc_auc": 0.75,
                    }
                )
            )

            result = verify_prediction_metrics(npz_path, json_path)

        self.assertEqual(result["num_samples"], 4)

    def test_verify_prediction_metrics_fails_on_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            npz_path = root / "predictions.npz"
            json_path = root / "aggregate.json"
            np.savez_compressed(
                npz_path,
                y_true=np.array([0, 1]),
                y_score=np.array([0.1, 0.9]),
                sample_id=np.array(["a", "b"], dtype=str),
            )
            json_path.write_text(
                json.dumps(
                    {
                        "sensitivity": 0.0,
                        "specificity": 1.0,
                        "balanced_accuracy": 0.5,
                        "roc_auc": 1.0,
                    }
                )
            )

            with self.assertRaises(AssertionError) as context:
                verify_prediction_metrics(npz_path, json_path)

        self.assertIn("sensitivity", str(context.exception))

    def test_verify_prediction_metrics_can_read_nested_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            npz_path = root / "predictions.npz"
            json_path = root / "training_summary.json"
            np.savez_compressed(
                npz_path,
                y_true=np.array([0, 0, 1, 1]),
                y_score=np.array([0.1, 0.8, 0.9, 0.4]),
                sample_id=np.array(["a", "b", "c", "d"], dtype=str),
            )
            json_path.write_text(
                json.dumps(
                    {
                        "test_metrics": {
                            "sensitivity": 0.5,
                            "specificity": 0.5,
                            "balanced_accuracy": 0.5,
                            "roc_auc": 0.75,
                        }
                    }
                )
            )

            result = verify_prediction_metrics(npz_path, json_path, metrics_key="test_metrics")

        self.assertEqual(result["num_samples"], 4)

    def test_persisting_predictions_requires_unshuffled_loader(self):
        loader = DataLoader(
            TensorDataset(torch.tensor([[-2.0], [0.0], [2.0]]), torch.tensor([0, 1, 1])),
            batch_size=2,
            shuffle=True,
        )

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as context:
                evaluate_loader(
                    IdentityLogitModel(),
                    loader,
                    nn.BCEWithLogitsLoss(),
                    torch.device("cpu"),
                    prediction_output_path=Path(tmp) / "predictions.npz",
                )

        self.assertIn("shuffle=False", str(context.exception))

    def test_evaluate_checkpoint_can_use_prediction_model_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image_root = root / "images"
            rows = ["path,label"]
            for label in ["normal", "pneumonia"]:
                label_dir = image_root / label
                label_dir.mkdir(parents=True)
                image_path = label_dir / f"{label}.png"
                Image.new("L", (32, 32), color=128).save(image_path)
                rows.append(f"{image_path},{label}")
            manifest = root / "chittagong_testing_manifest.csv"
            manifest.write_text("\n".join(rows) + "\n")
            checkpoint = root / "best.pt"
            model = build_model("pneumonia_net", pretrained=False, width=0.5)
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "model_name": "pneumonia_net",
                    "model_width": 0.5,
                    "image_size": 32,
                    "threshold": 0.5,
                },
                checkpoint,
            )

            evaluate_checkpoint(
                checkpoint,
                manifest_csv=manifest,
                device="cpu",
                prediction_output_root=root / "predictions",
                prediction_model_id="pneumonia_net_width_0_5",
            )

            self.assertTrue(
                (root / "predictions" / "chittagong" / "pneumonia_net_width_0_5.npz").exists()
            )

    def test_evaluate_checkpoint_writes_dataset_model_prediction_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image_root = root / "images"
            rows = ["path,label"]
            expected_sample_ids = []
            for label in ["normal", "pneumonia"]:
                label_dir = image_root / label
                label_dir.mkdir(parents=True)
                image_path = label_dir / f"{label}.png"
                Image.new("L", (32, 32), color=128).save(image_path)
                expected_sample_ids.append(str(image_path))
                rows.append(f"{image_path},{label}")
            manifest = root / "kermany_test_manifest.csv"
            manifest.write_text("\n".join(rows) + "\n")
            checkpoint = root / "best.pt"
            model = build_model("pneumonia_net", pretrained=False, width=0.5)
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "model_name": "pneumonia_net",
                    "model_width": 0.5,
                    "image_size": 32,
                    "threshold": 0.5,
                },
                checkpoint,
            )
            prediction_root = root / "predictions"

            evaluate_checkpoint(
                checkpoint,
                manifest_csv=manifest,
                device="cpu",
                prediction_output_root=prediction_root,
            )

            output_path = prediction_root / "kermany" / "pneumonia_net.npz"
            self.assertTrue(output_path.exists())
            with np.load(output_path) as payload:
                self.assertEqual(payload["y_true"].tolist(), [0, 1])
                self.assertEqual(payload["sample_id"].tolist(), expected_sample_ids)


class FrozenModuleTrainingTest(unittest.TestCase):
    def test_keep_frozen_modules_eval_preserves_batchnorm_stats(self):
        model = nn.Sequential(
            nn.BatchNorm1d(2),
            nn.Linear(2, 1),
        )
        for parameter in model[0].parameters():
            parameter.requires_grad = False
        model.train()

        keep_frozen_modules_eval(model)
        before = model[0].running_mean.clone()
        model(torch.ones(4, 2))

        self.assertFalse(model[0].training)
        self.assertTrue(model[1].training)
        self.assertTrue(torch.equal(model[0].running_mean, before))


class CheckpointMetadataTest(unittest.TestCase):
    def test_evaluate_checkpoint_rebuilds_pneumonia_net_with_saved_width(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            test_root = root / "images"
            rows = ["path,label"]
            for label in ["normal", "pneumonia"]:
                label_dir = test_root / label
                label_dir.mkdir(parents=True)
                image_path = label_dir / f"{label}.png"
                Image.new("L", (32, 32), color=128).save(image_path)
                rows.append(f"{image_path},{label}")
            manifest = root / "manifest.csv"
            manifest.write_text("\n".join(rows) + "\n")
            checkpoint = root / "best.pt"
            model = build_model("pneumonia_net", pretrained=False, width=0.5)
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "model_name": "pneumonia_net",
                    "model_width": 0.5,
                    "image_size": 32,
                    "threshold": 0.5,
                },
                checkpoint,
            )

            result = evaluate_checkpoint(
                checkpoint,
                manifest_csv=manifest,
                device="cpu",
                prediction_output_root=None,
            )

        self.assertEqual(result["num_samples"], 2)
        self.assertEqual(result["model_name"], "pneumonia_net")


if __name__ == "__main__":
    unittest.main()
