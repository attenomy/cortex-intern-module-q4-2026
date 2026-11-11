# Diagnostic error analysis: CTX-001 Intent Router

## 1. Protocol

- The test split was evaluated **once**, after the model, the temperature (T = 2.0) and the fallback rule (top probability below 0.60 routes to `search`) were frozen. Nothing was tuned afterwards.
- Clean test queries: n = 30 (10 finance, 5 support, 10 search, 5 orchestration). Ambiguous (mixed intent) test queries: n = 10, labelled with their main intent.
- With n = 30, one query is 3.3 percentage points. All accuracies below carry a wide interval (95% Wilson interval for the main result: 0.70 to 0.95).
- Raw output: `reports/test_evaluation.md` and `reports/test_evaluation.json`. Figure: `reports/figures/confusion_matrix.png`.
- Reproduce: `python api/modules/intent_router/training/evaluate_test.py --final` and `python api/modules/intent_router/training/eval_keyword_baseline.py`.

## 2. Results on the clean test queries (n = 30)

| system | argmax accuracy | end-to-end accuracy (with 0.60 fallback) | macro-F1 | fallback rate |
|---|---|---|---|---|
| Original keyword router | not applicable | 0.600 (18/30) | not computed | not applicable |
| TF-IDF + Logistic Regression | 0.800 (24/30) | 0.467 (14/30) | 0.406 | 0.70 |
| **Fine-tuned MiniLM (ONNX), T = 2.0** | 0.867 (26/30) | **0.867 (26/30)** | **0.840** | 0.20 |

For reference, the same MiniLM model scored 0.967 (29/30) on the clean validation queries. The drop to 0.867 is expected: the validation set was used to pick the best epoch and to fit the temperature, so it is an optimistic estimate, and the intervals overlap. The honest number for the report is the test result.

Per class (MiniLM, end to end):

| intent | precision | recall | F1 | support |
|---|---|---|---|---|
| finance | 0.91 | 1.00 | 0.95 | 10 |
| support | 0.80 | 0.80 | 0.80 | 5 |
| search | 0.82 | 0.90 | 0.86 | 10 |
| orchestration | 1.00 | 0.60 | 0.75 | 5 |

Confusion matrix (rows are the true intent, columns are the routed intent; fallbacks appear in the `search` column):

| true \ routed | finance | support | search | orchestration |
|---|---|---|---|---|
| finance | 10 | 0 | 0 | 0 |
| support | 0 | 4 | 1 | 0 |
| search | 1 | 0 | 9 | 0 |
| orchestration | 0 | 1 | 1 | 3 |

Orchestration has the weakest recall (3 of 5), and it is the smallest class in both training and test data.

How the original keyword router reached 0.600: it predicted `search` for 21 of the 30 queries because `search` is its default route. It therefore gets all 10 search queries right while getting only 5 of 10 finance, 2 of 5 support and 1 of 5 orchestration queries right. Its search recall is high only because it routes almost everything there.

How to read the TF-IDF row: its argmax accuracy (0.800) is only two queries below MiniLM's, which is within noise at this sample size. Its end-to-end accuracy collapses (0.467) because its probabilities are low, so 70% of queries fall below the 0.60 threshold and are sent to `search`. It is not calibrated for the rule the ticket requires.

## 3. Misclassifications (4 of 30 end to end)

| query | true | routed | confidence | top 3 | what happened |
|---|---|---|---|---|---|
| `La aplicación se cierra sola al abrir` | support | search (fallback) | 0.45 | finance 0.45, orchestration 0.29, search 0.22 | Spanish input. The raw top choice (finance) is also wrong. |
| `Define churn rate as used in our reports` | search | finance | 0.80 | finance 0.80, search 0.11, orchestration 0.06 | Confident error. Fallback cannot catch it. |
| `If the invoice is over 10k, send it to a manager for approval` | orchestration | search (fallback) | 0.53 | orchestration 0.53, finance 0.41, support 0.03 | The raw top choice was correct but fell just below 0.60, so fallback turned a correct answer into a wrong one. |
| `Retry the failed task three times, then alert me` | orchestration | support | 0.79 | support 0.79, orchestration 0.18, finance 0.02 | Confident error driven by the word "failed". |

## 4. What the fallback rule did on clean queries

The rule fired on 6 of 30 clean queries (20%, against 3% on validation):

- 4 were general knowledge `search` queries (`Meaning of RAG in simple words`, `What is the capital of France?`, `What is the time complexity of quicksort?`, `How tall is Mount Everest?`). Their group has no close relative in the training data, so the model is unsure, and falling back to `search` happens to be correct.
- 1 was the Spanish support query: wrong with or without fallback.
- 1 was the conditional orchestration query: the fallback made a correct raw answer wrong.

Net effect: raw argmax accuracy and end-to-end accuracy are both 26/30. Fallback rescued one query (`What is the capital of France?`, whose raw top choice was finance) and hurt one.

## 5. Ambiguous (mixed intent) queries (n = 10)

- Mean confidence is **0.88 on ambiguous queries against 0.80 on clean queries**. Mixed intent does not lower confidence on average, and only 1 of 10 falls back.
- 8 of 10 were routed to their labelled main intent. The two misses: `Check the invoice and trigger the payment flow` (finance 0.52 against orchestration 0.44, sent to search by fallback) and `Investigate the error and restart the pipeline` (support 0.95). The labels are judgement calls (this second query is both a support and an orchestration request).
- The unit test that compares `Generate invoice billing report after fixing crash bug` (confidence 0.661) with a clean finance query (0.969) passes, but that is one hand-picked query. Across the whole labelled group, the effect is not there.

## 6. The three largest failure modes (plus one interaction)

**F1. Non-English input.** The encoder (`all-MiniLM-L6-v2`) has an English vocabulary, and only 3 of the 200 training queries are non-English. The Spanish query got a flat, wrong distribution (0.45, 0.29, 0.22). Concrete changes: add non-English training examples for each intent, or evaluate a multilingual encoder (its size must be checked against the 250 MB limit first).

**F2. Confident errors driven by surface words.** `Define churn rate as used in our reports` (finance, 0.80) and `Retry the failed task three times, then alert me` (support, 0.79) show the model using words such as "reports" and "failed" as shortcuts. These errors have high confidence, so the 0.60 rule cannot catch them. Concrete changes: add hard negative training examples where the same words appear under a different intent, and grow the training set (200 queries is small). This is a data fix, not a threshold fix.

**F3. Mixed intent is not reflected in confidence.** On the labelled ambiguous group the model is more confident than on clean queries (0.88 against 0.80). A threshold on the top probability alone cannot detect mixed intent. Concrete changes: train with soft or multi-label targets, or add a margin rule (top probability minus second probability). The margin rule changes the fallback definition fixed by the ticket, so it needs the supervisor's approval.

**F4 (interaction). T = 2.0 trades in-domain confidence for noise rejection.** T was raised from 1.0 to 2.0 so that random noise and emoji fall below 0.60, which it does (noise strings scored about 0.40). The cost shows up here: the correct but low-margin orchestration query (0.53) was pushed under the threshold, and the fallback rate on clean queries is 20% on the test split against 3% on validation. T must not be re-fitted on the test split. The fix is a larger and more varied validation set, then re-fit.

## 7. Rejected alternatives and the evidence

| alternative | evidence | decision |
|---|---|---|
| Keyword matching (original `INTENT_MAPPINGS`) | 0.600 on clean test, 0.500 on ambiguous test; defaults to `search` for 21 of 30 queries; no notion of confidence | Replaced by the neural classifier |
| TF-IDF + Logistic Regression | 0.800 argmax, 0.467 with the 0.60 rule, macro-F1 0.406, 70% fallback | Kept only as the baseline |
| INT8 dynamic quantization | Single-call typical latency 1.36 ms against 2.90 ms, size 23 MB against 90 MB, same validation accuracy, but fallback rate 0.07 against 0.03. At 50 clients with 2 workers: 112 req/s, client p95 770 ms, router p50 119.8 ms. The cause was not investigated | Rejected |
| 2 or 3 worker processes | 588 and 648 req/s against 449 for one worker; client p95 154.5 and 127.6 ms against 121.2 ms; peak memory 450 and 612 MB against 217 MB | Rejected: no p95 gain and the memory is far above 250 MB |
| Cap on concurrent inferences, ONNX spin-wait off | In-process p99 up to 3.8 s and about 40% lower throughput than the default | Rejected, flags kept off |
| Batching (batch 4 and 16) | Throughput 597 and 650 items/s against 345, but each call takes 6.7 and 24.6 ms | Rejected: the API answers one query per request |
| Larger encoders (DistilBERT, BERT base) | Not benchmarked. Excluded by the memory and latency budget, which is an expectation from the parameter counts and not a measurement | Not evaluated |

## 8. Limitations

- 30 clean and 10 ambiguous test queries, written by one author: the intervals are wide and the labels for mixed queries are subjective.
- Training, validation and test queries come from the same hand-written topic groups, so the test split measures generalisation to unseen groups, not to real traffic.
- Training data has only 200 queries and 3 non-English examples.
- Latency was measured on one machine with the load generator on the same CPU.

## 9. Next steps, in priority order

1. Larger training and validation sets, with non-English examples and hard negatives (addresses F1 and F2).
2. Re-fit the temperature on the larger validation set and re-measure the fallback rate (addresses F4).
3. Ask the supervisor whether a margin-based fallback rule is acceptable (addresses F3).
