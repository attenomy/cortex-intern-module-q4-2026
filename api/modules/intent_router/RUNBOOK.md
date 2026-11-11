# Runbook: Intent Router (CTX-001)

Module: `api/modules/intent_router/`. Endpoint: `POST /api/v1/router`. Owner: Abhishek Adbhute. Supervisor: Saad Md.

## 1. What it does

Classifies a query into `finance`, `support`, `search` or `orchestration` with a fine-tuned MiniLM model served through ONNX Runtime on CPU. If the top probability is below 0.60 the answer is `search` with `fallback_triggered = true`. Every response also carries `top_k`, `target_pipeline`, `confidence` and `latency_ms`.

## 2. Prerequisites

| item | value |
|---|---|
| Python | 3.12 (tested) |
| Packages | `pip install -r api/requirements.txt` (includes `onnxruntime` and `tokenizers`; no torch or transformers at serving time) |
| Hardware | CPU only. Measured on 12 logical CPUs. Resident memory of the whole API process is about 190 to 220 MB |
| Model files | `api/modules/intent_router/models/` must contain `model.onnx`, `tokenizer.json`, `tokenizer_config.json`, `labels.json`, `calibration.json` |

**Open item:** `model.onnx` (90 MB) is not stored in git. Where the production artifact is kept (Git LFS, release asset or a build script) is waiting for a decision from the supervisor. Until then, copy the model folder to the host by hand.

## 3. Startup sequence

Start from the `api/` folder with a single worker:

```
cd api
uvicorn main:app --host 0.0.0.0 --port 8000
```

Do not use `--workers` greater than 1. Measured with 50 saturating clients, 2 and 3 workers gave no p95 improvement and used 2 to 3 times the memory.

What happens at startup (FastAPI lifespan of the intent router):

1. Read `labels.json` and `calibration.json` (temperature and maximum token length).
2. Load `tokenizer.json` and set truncation once.
3. Create the ONNX Runtime session (`ORT_ENABLE_ALL`, intra-op threads, CPU provider) and check that the model inputs are `input_ids` and `attention_mask`.
4. Run 3 warm-up inferences so the first real request has no cold-start cost.
5. Mark the service ready. Typical load plus warm-up time is 0.4 to 0.8 s.

If any step fails, the error is logged (`intent router failed to load`), the rest of the Cortex API still starts, and `/api/v1/router` answers **503** until the process is restarted with the problem fixed. There is no automatic retry.

Verify after every start:

```
curl -s -X POST http://localhost:8000/api/v1/router -H "Content-Type: application/json" -d '{"query": "Find invoice total for Q3 AWS"}'
curl -s http://localhost:8000/api/v1/router/metrics | grep model_ready
```

Expected: a JSON decision with `"intent_category": "finance"`, and `cortex_intent_router_model_ready 1`.

## 4. Environment flags

| variable | default | meaning |
|---|---|---|
| `INTENT_ROUTER_MODEL_DIR` | `api/modules/intent_router/models` | folder with the model files |
| `INTENT_ROUTER_MODEL_FILE` | `model.onnx` | model file name inside that folder |
| `INTENT_ROUTER_TEMPERATURE` | value in `calibration.json` (2.0) | softmax temperature. Lower values make the model more confident. Only change with a measurement behind it |
| `INTENT_ROUTER_THREADS` | `min(4, cpu count)` | ONNX Runtime intra-op threads. 1 thread measured no better under load |
| `INTENT_ROUTER_MAX_CONCURRENCY` | `0` (off) | cap on simultaneous inferences. Measured harmful (long tail), keep off |
| `INTENT_ROUTER_SPIN` | `1` | set `0` to stop ONNX worker threads busy-waiting. Measured no benefit |

Fixed in code, not configurable: fallback threshold 0.60, query limit 10,000 characters.

## 5. Error contract

| status | when | body |
|---|---|---|
| 200 | decision made (including fallback) | decision JSON |
| 400 | empty or whitespace-only query | `{"detail": "Query string cannot be empty"}` |
| 422 | missing field, wrong type, unknown field, over 10,000 characters, corrupt JSON | FastAPI validation error |
| 503 | model not loaded | `{"detail": "Intent router model is not ready"}` |
| 500 | unexpected failure | generic message; the stack trace is only in the log |

## 6. Metrics (Prometheus)

Exposed at `GET /api/v1/router/metrics`, text exposition format. Counters live in process memory and reset on restart.

| metric | type | meaning |
|---|---|---|
| `cortex_intent_router_model_ready` | gauge | 1 when the model is loaded and warmed up |
| `cortex_intent_router_requests_total{outcome}` | counter | `routed`, `fallback`, `bad_request` (400), `not_ready` (503), `error` (500) |
| `cortex_intent_router_intent_total{intent}` | counter | final intent per decision (fallbacks count as `search`) |
| `cortex_intent_router_latency_ms` | histogram | router execution time (the `latency_ms` field), buckets 1 to 1000 ms |

Requests rejected by validation (422) never reach the router code, so they are not counted here.

The shared telemetry module (`/metrics` and `/health`) currently returns placeholder values (fixed numbers and `model_loaded: true`). Do not use it for this service. Use the metrics above.

Useful queries and alert suggestions:

```
# p95 router execution time over 5 minutes (alert if above 50)
histogram_quantile(0.95, sum(rate(cortex_intent_router_latency_ms_bucket[5m])) by (le))

# fallback share (expected roughly 3 to 20 percent on the evaluation sets; a sudden rise suggests unusual input such as a new language)
rate(cortex_intent_router_requests_total{outcome="fallback"}[5m]) / (rate(cortex_intent_router_requests_total{outcome="routed"}[5m]) + rate(cortex_intent_router_requests_total{outcome="fallback"}[5m]))

# alert if the model is not ready, or if any 500 or 503 appears
cortex_intent_router_model_ready == 0
increase(cortex_intent_router_requests_total{outcome=~"error|not_ready"}[5m]) > 0
```

## 7. Performance reference (12 logical CPUs, one worker, 4 threads)

| measurement | result |
|---|---|
| Router execution time, 2,000 sequential calls | p50 2.30 ms, p95 3.87 ms, p99 11.04 ms |
| Open loop over HTTP, 50 to 400 req/s | client p95 27.6 to 44.6 ms, no errors |
| 50 saturating clients for 60 s | router p95 about 20 ms; client p95 above 100 ms because requests queue (capacity is about 450 to 530 req/s) |
| Memory over 5,000 requests | RSS growth 0.3 MB, no leak |

Full tables and the method are in `reports/tuning_experiments.md` and the `reports/load_test_results*.md` files.

## 8. Troubleshooting

| symptom | check | action |
|---|---|---|
| 503 on `/api/v1/router` | log line `intent router failed to load`; do the 5 model files exist in the model folder? | fix the files or `INTENT_ROUTER_MODEL_DIR`, restart |
| 503 only on the first request in a test | a test client was created without running the app lifespan | use `with TestClient(app)`; the service also lazy-loads once as a safety net |
| p95 above 50 ms | CPU shared with other heavy processes; very long inputs (cost grows with tokens up to the 64 token limit); request rate near capacity | reduce competing load; do not add workers; check the open-loop capacity table |
| fallback share rises | new input language or unusual phrasing | review recent queries; this is the signal to extend the training data |
| memory above 250 MB | RSS of the process | restart, then compare with the 190 to 220 MB baseline; report if it repeats |
| answers look worse after a change | temperature or model files changed | roll back (next section) |

## 9. Rollback

1. **Model or calibration:** keep the previous model folder next to the current one (for example `models_prev/`). Point `INTENT_ROUTER_MODEL_DIR` at it and restart. To undo only a temperature change set `INTENT_ROUTER_TEMPERATURE=1.0` or the previous value and restart.
2. **Code:** revert the merge commit of the CTX-001 pull request (`git revert -m 1 <merge commit>`) and redeploy. The original keyword router is in git history before that commit. It is much less accurate on the evaluation set (0.600 against 0.867) and has no confidence handling, so use it only as an emergency fallback.
3. After any rollback, run the verification commands from section 3 and confirm `cortex_intent_router_model_ready 1`.
