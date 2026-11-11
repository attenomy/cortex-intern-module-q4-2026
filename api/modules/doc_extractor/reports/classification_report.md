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
| `invoice` | 1.0000 | 1.0000 | 1.0000 | 54 |
| `receipt` | 0.5000 | 1.0000 | 0.6667 | 54 |
| `contract` | 1.0000 | 1.0000 | 1.0000 | 54 |
| `purchase_order` | 0.0000 | 0.0000 | 0.0000 | 54 |

## 3. Confusion Matrix

| Predicted -> | `invoice` | `receipt` | `contract` | `purchase_order` |
| :--- | :---: | :---: | :---: | :---: |
| Actual `invoice` | 54 | 0 | 0 | 0 |
| Actual `receipt` | 0 | 54 | 0 | 0 |
| Actual `contract` | 0 | 0 | 54 | 0 |
| Actual `purchase_order` | 0 | 54 | 0 | 0 |

## 4. Dataset Provenance
- Dataset contains locally generated synthetic document images.
- Original RVL-CDIP, SROIE, CUAD, and public purchase-order source records have not been verified.
- Results must not be interpreted as performance on the original public datasets.

## 5. Evaluation Methodology
- Strictly held-out 15% test partition evaluated with zero data leakage.
- Weights loaded from validated checkpoint `document_classifier.pth`.
- Ground truth comparison against canonical labels.