## Dataset Provenance Notice
The dataset used for this evaluation has unverified provenance.
Representative samples from all four classes appear synthetic or
template-generated. Original public dataset sources have not been
independently verified.
The metrics below describe performance on the current held-out test
split only. They must not be presented as benchmark results on RVL-CDIP,
SROIE, CUAD, or public Purchase Order datasets.
---
# CTX-002: Document Classifier Evaluation Report

## 1. Overall Test Metrics (Held-Out Split: 15%, Seed=42)

- **Model Architecture:** MobileNetV3-Small (`torchvision.models.mobilenet_v3_small`)
- **Accuracy:** 75.00%
- **Macro F1:** 0.6667 (Target: >= 0.90)
- **Macro Precision:** 0.6250
- **Macro Recall:** 0.7500
- **Target F1 Status:** DEFICIT (< 0.90)

## 2. Per-Class Performance Breakdown

| Document Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| `invoice` | 0.5000 | 1.0000 | 0.6667 | 54 |
| `receipt` | 1.0000 | 1.0000 | 1.0000 | 54 |
| `contract` | 1.0000 | 1.0000 | 1.0000 | 54 |
| `purchase_order` | 0.0000 | 0.0000 | 0.0000 | 54 |

## 3. Confusion Matrix

| Predicted -> | `invoice` | `receipt` | `contract` | `purchase_order` |
| :--- | :---: | :---: | :---: | :---: |
| Actual `invoice` | 54 | 0 | 0 | 0 |
| Actual `receipt` | 0 | 54 | 0 | 0 |
| Actual `contract` | 0 | 0 | 54 | 0 |
| Actual `purchase_order` | 54 | 0 | 0 | 0 |

## 4. Evaluation Methodology
- Strictly held-out 15% test partition evaluated with zero data leakage.
- Weights loaded from validated checkpoint `document_classifier.pth`.
- Ground truth comparison against canonical labels.