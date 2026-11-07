# SROIE Real-World Receipt Classification Evaluation

## Dataset
- Source: SROIE annotated receipt dataset
- Held-out test records: 337
- Successfully evaluated: 337
- Evaluation failures: 0
- Ground-truth class: receipt
- Model: MobileNetV3-Small, four output classes

## Results
- Receipt recall / accuracy: 0.8872
- Correct receipt predictions: 299/337
- Median model inference latency: 15.11 ms
- p95 model inference latency: 21.56 ms

## Predicted Class Distribution
| Predicted class | Count |
|---|---:|
| invoice | 1 |
| receipt | 299 |
| contract | 37 |
| purchase_order | 0 |

## Limitations
- This is a receipt-only evaluation, not a four-class benchmark.
- Accuracy here is receipt recall on the SROIE test split.
- Latency measures model inference only, excluding image decoding and OCR.
- Results do not establish the four-class Macro F1 acceptance target.

## Evaluation Failures
- None
