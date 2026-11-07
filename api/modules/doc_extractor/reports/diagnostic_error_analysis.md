# Diagnostic Error Analysis ? CTX-002
## 1. Evaluation Dataset
- Dataset: SROIE
- Split: Held-out test
- Document category: Receipt
- Total evaluated images: 337
- Image processing failures: 0
## 2. Classification Results
- Correctly predicted receipts: 299
- Misclassified receipts: 38
- Receipt recall: 88.72%
- Error rate: 11.28%
This is a receipt-only evaluation. It is NOT four-class Macro F1.
## 3. Misclassification Breakdown
| Predicted class | Count |
|---|---:|
| Contract | 37 |
| Invoice | 1 |
| Total | 38 |
## 4. Confidence Analysis
- Minimum error confidence: 0.3500
- Maximum error confidence: 0.9071
- Mean error confidence: 0.6138
| Confidence range | Errors |
|---|---:|
| 0.00?0.50 | 6 |
| 0.50?0.60 | 16 |
| 0.60?0.70 | 7 |
| 0.70?0.80 | 3 |
| 0.80?0.90 | 5 |
| 0.90?1.00 | 1 |
Six incorrect predictions had confidence above 0.80.
This indicates that confidence thresholding alone is unlikely to
resolve the observed classification errors.
## 5. Observations
- Contract is the dominant incorrect prediction.
- Real SROIE receipts are sometimes classified as contracts.
- The existing four-class training dataset was identified as
  synthetic/template-generated, with public-source provenance
  unverified.
- A synthetic-to-real visual domain mismatch is a plausible
  explanation, but has not been experimentally confirmed.
## 6. Limitations
- SROIE contains receipt examples only.
- This evaluation does not establish four-class Macro F1.
- No conclusion about contract, invoice, or purchase-order
  generalization can be drawn from this receipt-only test.
- The test split must remain held out and must not be used for
  retraining or hyperparameter tuning.
- Model inference latency is separate from full API/OCR latency.
## 7. Recommended Follow-up
1. Obtain verified real training data for all four classes.
2. Use training/validation data for domain adaptation experiments.
3. Evaluate on a fresh untouched test set.
4. Record per-class precision, recall, F1 and confusion matrix.
5. Re-run complete API and latency benchmarks after model changes.
## 8. Evidence
Misclassified sample details:
reports/sroie_misclassified_samples.json
Real SROIE evaluation:
reports/sroie_real_test_evaluation.md
