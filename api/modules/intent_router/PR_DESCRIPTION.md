### Attenomy Cortex Evidence-Driven Pull Request (EDPR)

---

#### 1. Ticket Identification & Architectural Decisions (ADR)
* **Ticket ID**: `[CTX-001]` Neural Semantic Intent Router & Sub-50ms CPU Inference Engine
* **Feature Branch**: `feature/CTX-001-intent-router`
* **Target Branch**: `staging`
* **Architectural Justification**:
  * The keyword router in `service.py` could not handle multi-intent text, paraphrases, other languages or noise. On the held-out test split it scored 0.600 accuracy and defaulted to `search` for 21 of 30 queries.
  * It is replaced by `all-MiniLM-L6-v2` fine-tuned on 200 labelled queries (4 intents) with a mean-pooling classification head, exported to ONNX and served with ONNX Runtime on CPU. The serving path uses only `onnxruntime`, `tokenizers` and `numpy` (no torch or transformers), which keeps the process around 190 to 220 MB resident.
  * Softmax uses a temperature (T = 2.0, fitted on validation, stored in `calibration.json`). If the top probability is below 0.60 the router returns `search` with `fallback_triggered = true`, as the ticket specifies. T = 2.0 is what makes random noise and emoji fall back.
  * The model and tokenizer are loaded and warmed up in the FastAPI lifespan of the intent router (3 warm-up inferences). A failed load does not crash the shared API: the endpoint answers 503. A one-time lazy load exists only as a safety net for callers that skip the lifespan (plain `TestClient(app)`).
  * Results on the test split (used once, after everything was frozen), clean queries n = 30: accuracy 0.867 (95% interval 0.70 to 0.95), macro-F1 0.840. Validation scored 0.967, which is optimistic because validation chose the epoch and T. Full analysis: `reports/diagnostic_error_analysis.md`.
* **Alternatives Considered & Rejected** (evidence in `reports/`):
  * Original keyword router: 0.600 on the clean test queries, no confidence handling.
  * TF-IDF + Logistic Regression: 0.800 raw accuracy, 0.467 with the 0.60 rule (its probabilities are low, 70% of queries fall back). Kept only as the baseline.
  * INT8 dynamic quantization: 2.1x faster per call and 4x smaller, but a higher fallback rate and an erratic latency tail; not adopted. *(update this line with the rerun load numbers)*
  * More than one worker process: no p95 improvement with 50 saturating clients and 2 to 3 times the memory. *(update with the rerun numbers)*
  * Concurrency cap and ONNX spin-wait off: long tail, lower throughput. One intra-op thread: no gain.
  * Batching: higher throughput but 6.7 to 24.6 ms per call; the API serves one query per request.
  * Larger encoders (DistilBERT, BERT base): not benchmarked, ruled out in advance by the memory and latency budget.
* **Deviations from the approved spec** (made to keep the existing API contract and tests working):
  * Empty or whitespace-only queries return HTTP 400 (existing behaviour and tests); other invalid payloads return 422.
  * `client_tier`, `max_routing_candidates`, `target_pipeline` and `cached` are kept. `top_k` has `min(max_routing_candidates, 4)` entries.
  * Added `GET /api/v1/router/metrics` (Prometheus text format) because the shared telemetry endpoint returns placeholder values.
* **Not in this PR**: `model.onnx` (90 MB) is not committed. Tests that need the model (all that classify text) require the model folder `api/modules/intent_router/models/` to be present; without it the endpoint returns 503 by design. Where the artifact should live (Git LFS, release asset or build script) is an open question for the supervisor.

---

#### 2. Automated Test Execution Evidence
Full, unfiltered output (also saved as `api/modules/intent_router/reports/pytest_output.txt`):

```text
python -m pytest modules/intent_router/tests/ -v
# PASTE THE RAW OUTPUT OF reports/pytest_output.txt HERE (46 passed)
```

* **Total Test Cases**: 46 collected cases (32 test functions) in `modules/intent_router/tests/test_intent_router.py`.
* **Edge-Case & Negative Test Ratio**: 24 of 32 test functions (75%) and 36 of 46 collected cases (78%) are negative, boundary or edge cases (empty and blank input, wrong types, over-length, unknown fields, corrupt JSON, noise and emoji fallback, injection strings, multilingual input, 50-thread concurrency, 503 before load, failed load, NaN logits, the exact 0.60 boundary, metrics counting).
* Existing regression suite (`python -m pytest -q` from `api/`): *(paste the result, expected 10 passed)*.

---

#### 3. Latency & Resource Profiling Proof
All numbers are from this machine (12 logical CPUs, CPU only, Windows 11, Python 3.12, onnxruntime 1.31). The load generator runs on the same machine. Raw tables are in `reports/`.

* **Benchmarking Tool**: custom asyncio/aiohttp load generator against a real `uvicorn main:app` (`profiling/load_test.py`), cProfile and a latency histogram (`profiling/profile_cprofile.py`), tracemalloc plus RSS (`profiling/memory_check.py`), 9 tuning runs (`profiling/bench_experiments.py`).
* **Concurrent Requests**: 50 concurrent clients for 60 seconds (closed loop, about 5% of requests are 10,000-character payloads), 527 req/s, about 31,600 requests.
* **Median Latency (p50)**: router execution time (`latency_ms` in each response) `8.1 ms`; end-to-end as seen by the client `94.0 ms`.
* **Tail Latency (p95)**: router execution time `17.9 ms` (under 50.0 ms). End-to-end client p95 is `109.1 ms`, **which is not under 50 ms**: with 50 clients that keep the server saturated, requests queue (by Little's law, 50 clients at 527 req/s is about 95 ms average). This is a capacity limit of this machine, not slow requests.
* **Error Rate**: `0.0%` (0 non-200 responses).
* **Realistic arrival rates** (open loop, requests arrive at a fixed rate, latency measured from the intended send time): client p95 27.6 ms at 50 req/s, 27.6 ms at 100, 28.9 ms at 200 and 44.6 ms at 400 req/s, no errors.
* **In-process, no HTTP** (2,000 calls): p50 2.30 ms, p90 2.86 ms, p95 3.87 ms, p99 11.04 ms.
* **Memory**: whole API process peak RSS 217 MB with 50 saturating clients (limit 250 MB). 5,000 requests: Python allocations +36 KB, RSS +0.3 MB (tracemalloc verdict PASS).
* **Question for the reviewer**: the ticket does not say whether "p95 under 50 ms" means the router's execution time or the end-to-end latency under saturation. The first is met with margin. The second is met at realistic request rates (up to 400 req/s) but not with 50 saturating clients on this machine.

---

#### 4. Video Demo Walkthrough
* **Video Link**: `PASTE THE LOOM LINK HERE`

---

#### 5. 2-Minute Code Defense Checklist
- [ ] I have line-by-line comprehension of all committed code and am prepared to defend it live.
- [ ] No hardcoded secrets, internal tokens, or sensitive API keys are committed.
- [ ] All failure modes and unparseable payloads return structured HTTP 4xx JSON errors, not unhandled 500 crashes.
- [ ] Model weights are pre-warmed during application startup (zero dynamic reloading per request).
- [ ] No em dashes or en dashes exist in documentation or code comments.

Notes for the reviewer: the only en or em dash characters in the module are four entries in the vocabulary of `models/tokenizer.json`, a third-party tokenizer file, not documentation or code comments. The one lazy load in `service.ensure_loaded()` runs only when the app lifespan did not (it is a no-op in production).
