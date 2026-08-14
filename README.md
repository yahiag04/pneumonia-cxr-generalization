# Pneumonia X-ray Classifier

Research code for an academic thesis on **binary pneumonia classification from
chest radiographs**, with particular attention to cross-dataset generalization,
decision thresholds, calibration, statistical model comparison, and
computational cost.

The main experiment trains five convolutional neural networks on a balanced,
adult-oriented subset of the RSNA Pneumonia Detection Challenge and evaluates
them on the internal RSNA test split and two external datasets. The central
result is that there is **no universally best architecture**: model rankings
change with the target domain, the evaluation metric, and the operating
threshold.

> **Research use only.** This repository is an academic prototype. It is not a
> medical device, has not been clinically validated, and must not be used for
> diagnosis or patient-care decisions.

## Contents

- [Research scope](#research-scope)
- [Experimental design](#experimental-design)
- [Models](#models)
- [Reference results](#reference-results)
- [Additional analyses](#additional-analyses)
- [Repository structure](#repository-structure)
- [Installation](#installation)
- [Data preparation](#data-preparation)
- [Core workflows](#core-workflows)
- [Outputs and reproducibility](#outputs-and-reproducibility)
- [Testing](#testing)
- [Limitations](#limitations)
- [Author and citation](#author-and-citation)

## Research scope

The project studies the classification of chest X-rays into two classes:

- `normal`;
- `pneumonia`.

The thesis is built around three questions:

1. Can a model trained on an adult, pneumonia-specific dataset retain its
   performance on independent external datasets?
2. Is one CNN architecture consistently better across internal and external
   domains?
3. How much of the observed ranking depends on discrimination, calibration,
   decision threshold, or computational capacity?

The work therefore goes beyond a single internal accuracy value. It compares
multiple architectures under the same training protocol, stores per-sample
scores, evaluates external-domain transfer without target-domain fine-tuning,
and performs paired statistical tests on predictions from the same samples.

## Experimental design

### Binary RSNA task

The primary training source is the
[RSNA Pneumonia Detection Challenge](https://www.kaggle.com/c/rsna-pneumonia-detection-challenge).
The original RSNA class descriptions are mapped as follows:

| RSNA class | Binary task |
| --- | --- |
| `Normal` | `normal` |
| `Lung Opacity` | `pneumonia` |
| `No Lung Opacity / Not Normal` | excluded |

The final balanced subset contains 7,000 radiographs:

| Split | Normal | Pneumonia | Total |
| --- | ---: | ---: | ---: |
| Train | 2,500 | 2,500 | 5,000 |
| Validation | 500 | 500 | 1,000 |
| Test | 500 | 500 | 1,000 |
| **Total** | **3,500** | **3,500** | **7,000** |

Splitting is performed at `patientId` level after retaining one image per
patient. Consequently, the train, validation, and test patient sets do not
overlap.

### External evaluation

The trained models are tested, without target-domain fine-tuning, on:

| Dataset | Normal | Pneumonia | Total | Role |
| --- | ---: | ---: | ---: | --- |
| Kermany | 234 | 390 | 624 | External pediatric-domain test |
| Chittagong | 257 | 256 | 513 | Independent external test |

Kermany is deliberately treated as an external test rather than the primary
training source because its pediatric population differs from the
adult-oriented RSNA setting. Chittagong provides a second independent domain
for studying how model behavior changes across datasets.

### Evaluation metrics

The primary threshold-dependent metric is **balanced accuracy**:

```text
balanced accuracy = (sensitivity + specificity) / 2
```

The evaluation pipeline also reports:

- accuracy, sensitivity, specificity, and F1-score;
- ROC-AUC and PR-AUC;
- confusion matrices;
- stratified bootstrap 95% confidence intervals;
- McNemar tests for paired binary decisions;
- DeLong tests for correlated ROC-AUC values;
- Holm-Bonferroni correction within each dataset and test family;
- Expected Calibration Error and Brier score;
- fixed, validation-selected, and oracle Youden thresholds.

Unless otherwise stated, the reference binary results below use a decision
threshold of `0.5`.

## Models

The main benchmark compares five architectures:

| Model | Initialization | Input | Parameters | GMAC at 224×224 |
| --- | --- | ---: | ---: | ---: |
| PneumoniaNet | From scratch | 1 channel | 300,161 | 0.5275 |
| ResNet18 | ImageNet | 3 channels | 11,177,025 | 1.8136 |
| MobileNetV3-Large | ImageNet | 3 channels | 4,203,313 | 0.2153 |
| EfficientNet-B0 | ImageNet | 3 channels | 4,008,829 | 0.3845 |
| DenseNet121 | ImageNet | 3 channels | 6,954,881 | 2.8331 |

`PneumoniaNet` is the custom architecture defined in
[`models/pneumonia_net.py`](models/pneumonia_net.py). It contains four
convolutional stages with channels `16 → 32 → 64 → 128`, batch normalization,
ReLU activations, max pooling, adaptive average pooling, and a compact binary
classification head. Its width is parameterized so that model-capacity scaling
can be studied without changing the overall design.

The comparison architectures are created through the central registry in
[`thesis/model_registry.py`](thesis/model_registry.py). The registry also
supports ResNet50 and EfficientNet B1-B3 for complementary experiments, but
they are not part of the five-model primary benchmark.

PneumoniaNet is the smallest model by parameter count. It is not the cheapest
model by operation count: MobileNetV3-Large has the lowest GMAC and the highest
balanced-accuracy-per-GMAC ratio in the reference benchmark.

## Reference results

The following values summarize the final five-model binary benchmark. They are
included as a reference snapshot of the thesis experiments; raw datasets and
trained checkpoints are intentionally not distributed in the repository.

### Balanced accuracy

| Model | RSNA test | Kermany | Chittagong |
| --- | ---: | ---: | ---: |
| PneumoniaNet | 0.896 | 0.688 | **0.830** |
| ResNet18 | 0.941 | 0.722 | 0.819 |
| MobileNetV3-Large | 0.944 | 0.787 | 0.797 |
| EfficientNet-B0 | **0.950** | 0.818 | 0.795 |
| DenseNet121 | 0.942 | **0.858** | 0.764 |

### ROC-AUC

| Model | RSNA test | Kermany | Chittagong |
| --- | ---: | ---: | ---: |
| PneumoniaNet | 0.961 | 0.789 | 0.887 |
| ResNet18 | 0.989 | 0.854 | 0.893 |
| MobileNetV3-Large | **0.990** | 0.874 | **0.904** |
| EfficientNet-B0 | 0.989 | 0.903 | 0.894 |
| DenseNet121 | 0.987 | **0.925** | 0.844 |

The main interpretation is intentionally cautious:

- EfficientNet-B0 has the highest balanced accuracy on the internal RSNA test,
  but paired tests do not clearly separate it from ResNet18,
  MobileNetV3-Large, or DenseNet121; it is clearly stronger than PneumoniaNet
  on that dataset.
- DenseNet121 is the strongest model on Kermany.
- PneumoniaNet has the highest threshold-0.5 balanced accuracy on Chittagong,
  but it is not significantly better than ResNet18, MobileNetV3-Large, or
  EfficientNet-B0. It is significantly better than DenseNet121 there.
- The model ranking therefore depends on the target domain and operating
  point. The results do not support claiming one universal winner.

## Additional analyses

### Zero-shot TorchXRayVision baselines

Three pretrained DenseNet121 models from
[TorchXRayVision](https://github.com/mlmed/torchxrayvision) are evaluated
without local training:

- `densenet121-res224-rsna`;
- `densenet121-res224-nih`;
- `densenet121-res224-all`.

They serve as an external sanity check for the local evaluation pipeline and
show that the source pretraining domain strongly affects zero-shot transfer.

### Threshold and calibration analysis

Per-sample probabilities are used as the canonical source for threshold,
calibration, and paired statistical analyses. The project compares:

- the fixed threshold `0.5`;
- the Youden threshold selected on the same test set, used only as an
  optimistic oracle diagnostic;
- a deployable threshold selected on RSNA validation and transferred to an
  external test set;
- temperature scaling fitted on RSNA validation and applied unchanged to test
  datasets.

The ranking is stable between threshold `0.5` and oracle Youden on RSNA and
Kermany, but changes substantially on Chittagong. Temperature scaling improves
some external calibration results but cannot, by itself, remove model-specific
domain shift. Because positive temperature scaling is monotonic in the logits,
it does not change binary predictions at threshold `0.5`.

### AP/PA projection control

RSNA metadata are used to stratify the internal test results by AP and PA
projection. All models obtain lower balanced accuracy on the AP subset in the
reference experiment, but projection and class are strongly associated in the
chosen split. The result is therefore descriptive rather than causal.
Equivalent DICOM view metadata are not available in the local external
manifests, so the same stratification cannot be repeated for Kermany and
Chittagong without additional annotation.

### Controlled capacity scaling

The scaling study compares:

- continuous width scaling of PneumoniaNet;
- official EfficientNet B0, B1, B2, and B3 variants.

On RSNA, performance is nearly flat across much of the tested capacity range.
On the external datasets, results fluctuate without a clear monotonic trend.
Since the current study uses one seed, these curves should be interpreted as a
within-protocol diagnostic, not as evidence of a general scaling law.

The tracked summary and plots are available here:

- [`outputs/scaling_study/scaling_study.csv`](outputs/scaling_study/scaling_study.csv)
- [`outputs/scaling_study/balanced_accuracy_vs_params.png`](outputs/scaling_study/balanced_accuracy_vs_params.png)
- [`outputs/scaling_study/balanced_accuracy_vs_gmac.png`](outputs/scaling_study/balanced_accuracy_vs_gmac.png)

<p align="center">
  <img src="outputs/scaling_study/balanced_accuracy_vs_params.png" alt="Balanced accuracy versus model parameters" width="82%">
</p>

### Exploratory three-class RSNA extension

The excluded RSNA category is reintroduced in an exploratory task with three
classes:

- `normal`;
- `lung_opacity`;
- `not_normal_no_lung_opacity`.

Each split is balanced per class: 2,500 training, 500 validation, and 500 test
images per class. Binary RSNA checkpoints initialize all compatible layers; the
final classifier is replaced with a three-output head. The reference experiment
uses only one adaptation epoch, freezes the comparison backbones, and briefly
fine-tunes PneumoniaNet end to end.

| Model | Macro balanced accuracy | Macro F1 | Third-class recall |
| --- | ---: | ---: | ---: |
| PneumoniaNet | 0.507 | 0.471 | 0.228 |
| ResNet18 | 0.677 | 0.674 | **0.478** |
| MobileNetV3-Large | **0.692** | **0.677** | 0.412 |
| EfficientNet-B0 | 0.687 | 0.663 | 0.340 |
| DenseNet121 | 0.687 | 0.670 | 0.380 |

This is a transfer-learning probe, not a definitive multi-class benchmark. The
low recall for `not_normal_no_lung_opacity` indicates that a full multi-epoch,
end-to-end training protocol and dedicated error analysis are needed.

## Repository structure

```text
pneumonia-xray-classifier/
├── models/                 # PneumoniaNet implementation
├── thesis/                 # Reusable data, training, metrics and analysis code
├── scripts/                # Command-line experiment entry points
├── tests/                  # Unit tests
├── outputs/                # Generated results; mostly ignored by Git
├── requirements.txt        # Python dependencies
└── README.md
```

Important reusable modules include:

| Path | Purpose |
| --- | --- |
| `thesis/data.py` | ImageFolder and CSV-manifest datasets, preprocessing, loaders |
| `thesis/train.py` | Binary training, early stopping, device selection, checkpoints |
| `thesis/train_multiclass.py` | Three-class transfer and training pipeline |
| `thesis/metrics.py` | Binary evaluation metrics |
| `thesis/metrics_canonical.py` | Metrics recomputed from canonical per-sample scores |
| `thesis/predictions.py` | Prediction persistence and loading |
| `thesis/stat_tests.py` | Bootstrap, McNemar, DeLong, and multiplicity correction |
| `thesis/calibration.py` | ECE, Brier score, and calibration summaries |
| `thesis/temperature_scaling.py` | Source-validation temperature scaling |
| `thesis/threshold_analysis.py` | Threshold ranking and ROC analysis |
| `thesis/model_complexity.py` | Parameter and GMAC profiling |
| `thesis/model_registry.py` | Central model construction and metadata |

Every command-line entry point supports `--help`. The sections below document
the main end-to-end workflows.

## Installation

### Requirements

- Python 3.10 or newer;
- enough disk space for the selected X-ray datasets and generated checkpoints;
- a CUDA GPU or Apple Silicon MPS device is recommended for training, but CPU
  execution is supported.

The runtime automatically selects MPS, then CUDA, then CPU when `--device` is
not specified. Pass `--device cuda`, `--device mps`, or `--device cpu` to
override automatic selection.

### Environment setup

```bash
git clone https://github.com/yahiag04/pneumonia-xray-classifier.git
cd pneumonia-xray-classifier

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The dependency set includes PyTorch, torchvision, scikit-learn, NumPy,
Matplotlib, Seaborn, Pillow, pydicom, and TorchXRayVision.

## Data preparation

Datasets are not distributed with this repository. Downloading and using them
is subject to each source's terms and access requirements.

### Accepted RSNA source layouts

The RSNA preparation scripts recognize either of these layouts beneath
`--rsna-root`:

```text
# Original competition DICOM layout
stage_2_detailed_class_info.csv
stage_2_train_images/
```

```text
# Processed PNG layout
stage2_train_metadata.csv
Training/Images/
```

DICOM images are converted during preparation. Existing processed images can
be hard-linked, symlinked, or copied according to `--link-mode`.

### Prepare the binary RSNA subset

```bash
python scripts/prepare_rsna_binary.py \
  --rsna-root /path/to/rsna-pneumonia-detection-challenge \
  --output-root data/rsna_binary_size_matched \
  --train-per-class 2500 \
  --val-per-class 500 \
  --test-per-class 500 \
  --seed 42
```

The resulting directory follows torchvision's `ImageFolder` convention:

```text
data/rsna_binary_size_matched/
├── train/
│   ├── normal/
│   └── pneumonia/
├── val/
│   ├── normal/
│   └── pneumonia/
├── test/
│   ├── normal/
│   └── pneumonia/
└── metadata.csv
```

Use `--overwrite` only when intentionally replacing an existing prepared
dataset. The default `--link-mode auto` chooses a suitable local strategy;
explicit options are `hardlink`, `symlink`, and `copy`.

### External manifest format

External datasets are read from CSV files with exactly two semantic fields:

```csv
path,label
/absolute/path/to/normal/image_001.png,normal
/absolute/path/to/pneumonia/image_002.png,pneumonia
```

Binary labels must be lowercase `normal` or `pneumonia`. Absolute paths are the
least ambiguous choice. Relative paths must be valid from the working directory
used to run the command.

### Prepare the three-class RSNA subset

```bash
python scripts/prepare_rsna_multiclass.py \
  --rsna-root /path/to/rsna-pneumonia-detection-challenge \
  --output-root data/rsna_multiclass_size_matched \
  --train-per-class 2500 \
  --val-per-class 500 \
  --test-per-class 500 \
  --seed 42
```

## Core workflows

### 1. Run the five-model adult RSNA benchmark

The following command trains all five primary models, evaluates the internal
RSNA test during training, and evaluates both external manifests:

```bash
python scripts/run_adult_branch.py \
  --data-root data/rsna_binary_size_matched \
  --manifest kermany=/path/to/kermany_test_manifest.csv \
  --manifest chittagong=/path/to/chittagong_test_manifest.csv \
  --output-dir outputs/runs_rsna_adult \
  --eval-output-dir outputs/evaluations/rsna_adult \
  --epochs 20 \
  --batch-size 32 \
  --lr 3e-4 \
  --patience 5 \
  --seed 42
```

To train only selected architectures, repeat `--model`:

```bash
python scripts/run_adult_branch.py \
  --model pneumonia_net \
  --model efficientnet_b0 \
  --data-root data/rsna_binary_size_matched
```

Supported primary model names are `pneumonia_net`, `resnet18`,
`mobilenet_v3_large`, `efficientnet_b0`, and `densenet121`.

### 2. Evaluate one binary checkpoint

```bash
python scripts/evaluate_model.py \
  --checkpoint outputs/runs_rsna_adult/efficientnet_b0/best.pt \
  --manifest /path/to/external_test_manifest.csv \
  --output outputs/evaluations/efficientnet_b0_external.json
```

For an internal ImageFolder test split, use `--data-root` instead of
`--manifest`. Current checkpoints include model metadata; `--model` is needed
only for legacy checkpoints that do not contain it.

### 3. Run zero-shot TorchXRayVision evaluation

```bash
python scripts/evaluate_torchxrayvision.py \
  --manifest /path/to/external_test_manifest.csv \
  --weights densenet121-res224-rsna \
  --weights densenet121-res224-nih \
  --weights densenet121-res224-all \
  --output-dir outputs/evaluations/torchxrayvision_zero_shot
```

This workflow may download pretrained weights on first use.

### 4. Profile model complexity

```bash
python scripts/profile_model_complexity.py \
  --output-dir outputs/model_complexity
```

The profiler reports trainable and total parameters and MAC/GMAC estimates.
Pass `--performance-csv /path/to/adult_branch_summary.csv` to join a compatible
performance table and calculate balanced accuracy per GMAC.

### 5. Select and transfer a decision threshold

```bash
python scripts/select_thresholds.py \
  --checkpoint outputs/runs_rsna_adult/efficientnet_b0/best.pt \
  --val-data-root data/rsna_binary_size_matched \
  --test-manifest /path/to/chittagong_test_manifest.csv \
  --metric balanced_accuracy \
  --output-json outputs/thresholds/efficientnet_b0.json \
  --output-csv outputs/thresholds/efficientnet_b0.csv
```

Exactly one validation source must be supplied: `--val-data-root` or
`--val-manifest`. A test source is optional and follows the same convention.
Use `--min-sensitivity` when threshold selection must satisfy a minimum
sensitivity constraint.

### 6. Compare models statistically

```bash
python scripts/compare_model_statistics.py \
  --checkpoint pneumonia_net=outputs/runs_rsna_adult/pneumonia_net/best.pt \
  --checkpoint resnet18=outputs/runs_rsna_adult/resnet18/best.pt \
  --checkpoint mobilenet_v3_large=outputs/runs_rsna_adult/mobilenet_v3_large/best.pt \
  --checkpoint efficientnet_b0=outputs/runs_rsna_adult/efficientnet_b0/best.pt \
  --checkpoint densenet121=outputs/runs_rsna_adult/densenet121/best.pt \
  --manifest rsna=/path/to/rsna_test_manifest.csv \
  --manifest kermany=/path/to/kermany_test_manifest.csv \
  --manifest chittagong=/path/to/chittagong_test_manifest.csv \
  --output-dir outputs/statistical_tests
```

The analysis computes predictions in memory, then writes bootstrap confidence
intervals and paired model-comparison tables. Keeping the exact same manifest
order for every model is essential for paired tests. Use the standard
evaluation workflow when persistent `.npz` prediction files are also needed.

### 7. Run the controlled scaling study

```bash
python scripts/run_scaling_study.py \
  --data-root data/rsna_binary_size_matched \
  --manifest kermany=/path/to/kermany_test_manifest.csv \
  --manifest chittagong=/path/to/chittagong_test_manifest.csv \
  --family all \
  --output-dir outputs/scaling_study \
  --seed 42
```

Use `--family pneumonia_net` or `--family efficientnet` to run only one curve.
The script also exposes repeated `--pneumonia-width`, repeated
`--efficientnet-variant`, `--train-size`, and `--seed` options for controlled
follow-up experiments.

### 8. Train and evaluate the exploratory three-class task

Train a transferred MobileNetV3-Large classifier for the reference one-epoch
probe:

```bash
python scripts/train_multiclass_model.py \
  --data-root data/rsna_multiclass_size_matched \
  --model mobilenet_v3_large \
  --init-checkpoint outputs/runs_rsna_adult/mobilenet_v3_large/best.pt \
  --freeze-backbone \
  --epochs 1 \
  --lr 3e-4 \
  --seed 42
```

Evaluate the resulting checkpoint:

```bash
python scripts/evaluate_multiclass_model.py \
  --checkpoint outputs/runs_rsna_multiclass/mobilenet_v3_large/best.pt \
  --data-root data/rsna_multiclass_size_matched \
  --output outputs/evaluations/rsna_multiclass/mobilenet_v3_large.json
```

For the reference PneumoniaNet experiment, omit `--freeze-backbone` so that all
compatible transferred layers remain trainable.

## Outputs and reproducibility

Training and analysis commands generate combinations of:

- `best.pt` checkpoints containing model and configuration metadata;
- JSON and CSV metric summaries;
- canonical per-sample prediction arrays in `.npz` format;
- bootstrap intervals and paired statistical-test tables;
- ROC, calibration, threshold, and scaling plots;
- dataset metadata describing the prepared split.

Most generated files under `data/` and `outputs/` are excluded from Git because
they are large, derived, or machine-specific. The repository also excludes
raw radiographs, checkpoints (`.pt`, `.pth`, `.ckpt`), local virtual
environments, caches, and compiled thesis artifacts. A fresh clone therefore
contains the code and selected lightweight reference summaries, not the full
experimental state.

For the closest possible reproduction:

1. use the documented per-class sample counts and `seed=42`;
2. retain the generated `metadata.csv` and external manifests;
3. record the Python, PyTorch, torchvision, accelerator, and operating-system
   versions;
4. keep per-sample predictions, not only aggregate metrics;
5. repeat training with multiple seeds before interpreting small differences
   as architecture effects.

PyTorch runs on different devices may still show residual non-determinism even
when the data split and random seed are fixed.

## Testing

Run the complete unit-test suite from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

Inspect any command without starting an experiment:

```bash
python scripts/run_adult_branch.py --help
python scripts/compare_model_statistics.py --help
python scripts/run_scaling_study.py --help
```

## Limitations

- The external datasets differ in population, acquisition protocol, label
  definition, and class balance; cross-dataset differences cannot be
  attributed to architecture alone.
- AP/PA projection is only partially controlled because equivalent view
  metadata are unavailable in the local external manifests.
- The primary benchmark uses one controlled training seed. Bootstrap intervals
  quantify test-sample uncertainty, not training-run variability.
- The main operating point is threshold `0.5`. Oracle Youden results are
  diagnostic upper bounds and are not deployable estimates.
- Calibration and thresholds fitted on RSNA validation need not transfer to an
  external domain.
- The balanced RSNA subset provides a controlled comparison but does not use
  all information available in the original competition dataset.
- The three-class experiment is deliberately preliminary and uses only one
  epoch of adaptation.
- No clinical validation, prospective study, fairness assessment, or
  deployment safety evaluation has been performed.

## Author and citation

Developed by **Yahia Ghallale** as an academic thesis project at the University
of Brescia.

If this repository supports academic work, cite it as software and include the
specific commit hash used for the experiments:

```bibtex
@software{ghallale2026pneumonia,
  author = {Ghallale, Yahia},
  title = {Pneumonia X-ray Classifier},
  year = {2026},
  url = {https://github.com/yahiag04/pneumonia-xray-classifier}
}
```
