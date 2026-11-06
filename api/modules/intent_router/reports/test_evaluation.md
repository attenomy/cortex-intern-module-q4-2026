# Test split evaluation (run once, configuration frozen)
Temperature T = 2.0; fallback rule: top probability < 0.60 routes to `search`.
## Clean test queries (n=30)
| model | argmax acc | end-to-end acc (with fallback) | 95% interval | macro-F1 | fallback rate |
|---|---|---|---|---|---|
| fine-tuned MiniLM (ONNX) | 0.867 | 0.867 (26/30) | 0.70 to 0.95 | 0.840 | 0.20 |
| TF-IDF + Logistic Regression | 0.800 | 0.467 | | 0.406 | 0.70 |

Per-class (MiniLM, end to end):

```
               precision    recall  f1-score   support

      finance       0.91      1.00      0.95        10
      support       0.80      0.80      0.80         5
       search       0.82      0.90      0.86        10
orchestration       1.00      0.60      0.75         5

     accuracy                           0.87        30
    macro avg       0.88      0.83      0.84        30
 weighted avg       0.88      0.87      0.86        30
```
Confusion matrix (rows = true, columns = routed; the `search` column includes fallbacks):

```
             financ  suppor  search  orches
finance          10       0       0       0
support           0       4       1       0
search            1       0       9       0
orchestration      0       1       1       3
```

## Errors on clean test queries (4)
- `La aplicación se cierra sola al abrir`: true **support**, routed **search** (fallback: True), confidence 0.45; top-3: finance 0.45, orchestration 0.29, search 0.22
- `Define churn rate as used in our reports`: true **search**, routed **finance** (fallback: False), confidence 0.80; top-3: finance 0.80, search 0.11, orchestration 0.06
- `If the invoice is over 10k, send it to a manager for approval`: true **orchestration**, routed **search** (fallback: True), confidence 0.53; top-3: orchestration 0.53, finance 0.41, support 0.03
- `Retry the failed task three times, then alert me`: true **orchestration**, routed **support** (fallback: False), confidence 0.79; top-3: support 0.79, orchestration 0.18, finance 0.02

## Fallbacks on clean test queries (6)
- `La aplicación se cierra sola al abrir` (true support): confidence 0.45; top-3: finance 0.45, orchestration 0.29, search 0.22
- `Meaning of RAG in simple words` (true search): confidence 0.50; top-3: search 0.50, finance 0.22, orchestration 0.19
- `What is the capital of France?` (true search): confidence 0.45; top-3: finance 0.45, search 0.35, support 0.12
- `What is the time complexity of quicksort?` (true search): confidence 0.32; top-3: search 0.32, finance 0.31, orchestration 0.27
- `How tall is Mount Everest?` (true search): confidence 0.53; top-3: search 0.53, finance 0.23, support 0.14
- `If the invoice is over 10k, send it to a manager for approval` (true orchestration): confidence 0.53; top-3: orchestration 0.53, finance 0.41, support 0.03

## Ambiguous (mixed-intent) test queries (n=10)
Mean confidence 0.88 vs 0.80 on clean queries; fallback rate 0.10.

- `The invoice page crashes when I open it` (main intent support): routed support, confidence 0.84; top-3: support 0.84, finance 0.13, orchestration 0.02
- `I need help, the search bar stopped working` (main intent support): routed support, confidence 0.96; top-3: support 0.96, search 0.02, finance 0.01
- `Billing portal shows an error on login` (main intent support): routed support, confidence 0.93; top-3: support 0.93, finance 0.05, search 0.02
- `Workflow fails with a timeout, please check the logs` (main intent support): routed support, confidence 0.96; top-3: support 0.96, orchestration 0.02, finance 0.01
- `Fix the crash and then let me know` (main intent support): routed support, confidence 0.95; top-3: support 0.95, orchestration 0.02, search 0.01
- `Search the policy docs and then run the approval workflow` (main intent orchestration): routed orchestration, confidence 0.89; top-3: orchestration 0.89, support 0.06, search 0.04
- `Check the invoice and trigger the payment flow` (main intent orchestration): routed search, confidence 0.52; top-3: finance 0.52, orchestration 0.44, support 0.02
- `Investigate the error and restart the pipeline` (main intent orchestration): routed support, confidence 0.95; top-3: support 0.95, orchestration 0.03, search 0.01
- `Look up the vendor, then start the onboarding workflow` (main intent orchestration): routed orchestration, confidence 0.89; top-3: orchestration 0.89, search 0.06, support 0.04
- `Find the latest report and email it to the team automatically` (main intent orchestration): routed orchestration, confidence 0.95; top-3: orchestration 0.95, support 0.03, finance 0.01
