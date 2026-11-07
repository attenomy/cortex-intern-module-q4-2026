# Loom script and code defense prep (personal notes, not for the repo)

## Part A. Loom walkthrough, target 75 to 85 seconds

Prepare before recording: stop any old server, open two terminals in the repo root, and open `http://localhost:8000/docs` in the browser. Using the `/docs` page avoids PowerShell quoting problems with JSON.

| time | show | say (short) |
|---|---|---|
| 0:00 | terminal | "This is CTX-001, the neural intent router. It replaces keyword matching with a fine-tuned MiniLM model served through ONNX Runtime on CPU." |
| 0:08 | `cd api` then `uvicorn main:app` | "The model loads and warms up at startup, so the first request has no cold start." Point at the startup finishing. |
| 0:18 | `/docs`, POST `/api/v1/router`, query `Find invoice total for Q3 AWS` | "A clear query routes to finance with high confidence. The response has the top three candidates, the pipeline and the router's own latency." |
| 0:30 | same page, query `xkq9#@!zz` | "Noise gets low confidence, so the 0.60 rule sends it to search with fallback_triggered true." |
| 0:40 | empty query, then `{"query": 123}` | "Failure modes return structured errors: 400 for an empty query, 422 for a wrong type. No 500 crashes." |
| 0:52 | open `/api/v1/router/metrics` in the browser | "Prometheus counters for outcomes, intents, a latency histogram and model readiness." |
| 1:00 | second terminal: `cd api` then `python -m pytest modules/intent_router/tests/ -q` | "46 tests pass, 75 percent of the test functions are negative or boundary cases." |
| 1:12 | `reports/figures/latency_histogram.png` or `reports/load_test_results.md` | "Router execution time is about 8 ms median and 18 ms p95 with 50 concurrent clients. End to end, p95 is under 50 ms up to 400 requests per second, and about 110 ms when 50 clients saturate this machine. I report both." |
| 1:22 | stop | "Evidence, error analysis and runbook are in the PR." |

## Part B. 2-minute code defense: the story to tell

1. **Problem:** keyword matching: 0.600 on the test split, no confidence, fails on multi-intent and other languages.
2. **Solution in one line:** tokenizer, MiniLM encoder, mean pooling, linear head, softmax with temperature, 0.60 fallback, ONNX Runtime on CPU.
3. **Result:** test accuracy 0.867 (26/30, interval 0.70 to 0.95); router p95 about 4 ms in-process and about 18 ms under 50 clients.
4. **Honest limits to volunteer:** 30 test queries; confident errors on words like "reports" and "failed"; mixed-intent queries are not less confident (0.88 against 0.80); Spanish input fails; end-to-end p95 under 50 saturating clients is about 110 ms.

## Part C. Tensor walk-through (be able to say this without notes)

| step | shape | what happens |
|---|---|---|
| tokenizer | `input_ids` (1, L), `attention_mask` (1, L), int64, L at most 64 | text to word piece ids; long input is truncated (cost is bounded) |
| encoder (6 layers) | (1, L, 384) | self-attention mixes tokens; one 384 number vector per token |
| mean pooling | (1, 384) | `sum(h * mask) / sum(mask)`: average over real tokens only, padding is masked out. MiniLM was pre-trained to make sentence vectors this way |
| linear head | (1, 4) | 384 to 4 logits, one per intent (dropout is training only) |
| softmax with T | (4,) | `exp(z/T)` over the sum; subtract the maximum first so nothing overflows; T = 2.0 flattens the distribution |
| decision | scalar | if max probability is below 0.60 the answer is `search` with fallback; otherwise the argmax |
| top-k | list | `argsort(-p)`, first `max_routing_candidates`, at most 4 |

Why a temperature: it rescales confidence without changing the ranking. A higher T makes noise fall under 0.60, at the cost of pushing some correct but low-margin queries under it too (one such case in the test split).

## Part D. Likely questions and short answers

- **Why ONNX Runtime and not PyTorch?** Smaller serving image and memory (no torch), graph optimizations, no Python overhead in the model call. Verified the ONNX output matches PyTorch.
- **Why MiniLM and not DistilBERT?** About 22M parameters and a 90 MB FP32 file fits the 250 MB limit with room; DistilBERT was ruled out by the budget and not benchmarked.
- **Where is thread safety?** Request threads only read shared objects: the ONNX session (`run` is thread safe), the tokenizer (truncation set once at load), the label list and temperature. Nothing per request is stored on `self`. The metrics counters use a lock; the lazy load uses a lock. A test runs 500 calls on 50 threads and checks the results are identical.
- **What happens if the model fails to load?** The lifespan catches it, logs it, the rest of the API starts, and the router answers 503. No automatic retry.
- **What if the model outputs NaN?** The probabilities become uniform (0.25 each), so the fallback rule fires and the request is routed to `search`; the error is logged.
- **What does warm-up do?** Three dummy inferences at startup remove the first-call cost (memory allocation and lazy initialization).
- **Why 400 for empty but 422 for wrong type?** The existing contract and tests expect 400 for empty or blank queries; type and schema errors come from request validation (422).
- **Why not more workers or INT8?** Measured: no p95 gain and 2 to 3 times the memory for workers; INT8 was faster per call but had a higher fallback rate and an erratic tail. Say which of those numbers were rerun if asked.
- **What is Little's law and why does it matter here?** In a closed-loop test, average latency is about clients divided by throughput. With 50 clients and 527 req/s that is about 95 ms. Getting under 50 ms would need about twice the capacity.
- **How do you know the test set was not used for tuning?** It was evaluated once by `evaluate_test.py --final`, after the model, T and threshold were frozen. T was fitted on validation.
- **What would you do next?** More training data with non-English examples and hard negatives, re-fit T on a larger validation set, and ask whether a margin-based fallback is acceptable.

## Part E. Numbers to know

| item | value |
|---|---|
| Test accuracy (clean, n = 30) | 0.867 (validation 0.967) |
| Keyword router, TF-IDF baseline | 0.600, 0.467 end to end (0.800 raw) |
| Router execution time, 50 saturating clients | p50 8.1 ms, p95 17.9 ms |
| End-to-end, 50 saturating clients | p50 94.0 ms, p95 109.1 ms, 527 req/s |
| End-to-end, open loop 50 to 400 req/s | p95 27.6 to 44.6 ms |
| Memory | 217 MB peak (whole API), no leak over 5,000 requests |
| Tests | 46 cases, 32 functions, 75 percent negative or boundary |
