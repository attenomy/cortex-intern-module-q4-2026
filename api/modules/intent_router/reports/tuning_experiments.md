# Tuning experiments and latency evidence: CTX-001 Intent Router

All numbers were measured by the scripts in `profiling/` and are stored next to this file as `bench_results.*`, `load_test_results*.*`, `cprofile_*`, `latency_percentiles.json` and `memory_check.*`.

## 1. Setup

| | |
|---|---|
| Hardware | Intel64 Family 6 Model 186, 12 logical CPUs, 16.8 GB RAM, Windows 11, CPU only (no GPU) |
| Software | Python 3.12.10, onnxruntime 1.31.1, tokenizers (no torch or transformers at serving time) |
| Model | `all-MiniLM-L6-v2` fine-tuned for 4 intents, exported to ONNX (FP32, 90 MB) |
| Decision rule | softmax with temperature T = 2.0; if the top probability is below 0.60 the router returns `search` with `fallback_triggered = true` |
| Accuracy data | 30 clean validation queries (test split not used for any tuning decision) |
| Machine conditions | plugged in, power mode "Best performance", other applications closed *(edit if different)* |

## 2. Experiment runs (9 runs, `bench_experiments.py`)

"typical" = dataset queries; "worst case" = one 10,000-character payload. Batch rows report latency per call. Accuracy is end to end (with the 0.60 fallback) on the 30 clean validation queries.

| ID | model | threads | max_len | batch | typical p50 / p95 (ms) | worst-case p50 / p95 (ms) | items/s | size MB | clean acc | fallback rate |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | fp32 | 4 | 64 | 1 | 2.90 / 4.04 | 12.53 / 15.20 | 345 | 90 | 0.967 | 0.03 |
| E2 | fp32 | 4 | 128 | 1 | 2.77 / 3.77 | 17.53 / 20.57 | 362 | 90 | 0.967 | 0.03 |
| E3 | fp32 | 4 | 256 | 1 | 2.20 / 2.86 | 25.41 / 29.94 | 454 | 90 | 0.967 | 0.03 |
| E4 | fp32 | 4 | 64 | 4 | 6.70 / 8.75 | 27.73 / 38.15 | 597 | 90 | 0.967 | 0.03 |
| E5 | fp32 | 4 | 64 | 16 | 24.63 / 31.90 | 93.25 / 116.08 | 650 | 90 | 0.967 | 0.03 |
| E6 | int8 | 4 | 64 | 1 | 1.36 / 1.76 | 13.36 / 29.00 | 734 | 23 | 0.967 | 0.07 |
| E7 | int8 | 4 | 256 | 1 | 3.56 / 7.54 | 19.22 / 68.91 | 281 | 23 | 0.967 | 0.07 |
| E8 | fp32 | 1 | 64 | 1 | 6.00 / 10.35 | 25.75 / 37.65 | 167 | 90 | 0.967 | 0.03 |
| E9 | fp32 | 2 | 64 | 1 | 3.17 / 4.13 | 15.14 / 15.72 | 316 | 90 | 0.967 | 0.03 |

**Findings**
- **Sequence length** only changes the worst case, because the cost grows with the number of tokens kept: 12.5 ms (64 tokens), 17.5 ms (128), 25.4 ms (256) at p50. Typical queries are under 30 tokens and are unaffected. Accuracy is identical in all three runs because the validation queries are short, so this experiment says nothing about accuracy on long queries.
- **Threads:** 2 threads reach about 91% of the 4-thread speed (3.17 vs 2.90 ms p50); 1 thread is about twice as slow (6.00 ms).
- **INT8 (dynamic quantization)** is about 2.1x faster on typical queries (1.36 vs 2.90 ms) and 4x smaller (23 vs 90 MB) with the same clean accuracy. However the fallback rate rose from 0.03 to 0.07 (2 vs 1 of 30 queries), because T was fitted on the FP32 model, and its worst-case tail was erratic (E7 p95 68.9 ms vs 29.94 ms for FP32 at the same length). Not adopted yet.
- **Batching** raises throughput (650 vs 345 items/s at batch 16) but each call takes 24.6 ms. The API answers one query per request, so batching would need request grouping and would add latency. Not adopted.

## 3. Concurrency experiments (in-process, `load_test.py --inprocess`)

N threads call `route_query` directly (no HTTP). Closed loop: each thread sends its next request as soon as the previous one returns.

| configuration | concurrency | req/s | p50 | p95 | p99 |
|---|---|---|---|---|---|
| default (unlimited, 4 threads, spinning on) | 1 | 335 | 2.4 | 6.0 | 12.1 |
| | 10 | 970 | 8.7 | 24.4 | 30.0 |
| | 50 | 971 | 32.0 | 111.8 | 181.6 |
| `MAX_CONCURRENCY=2` | 1 | 358 | 2.2 | 7.1 | 11.9 |
| | 10 | 572 | 2.9 | 13.1 | 439.3 |
| | 50 | 560 | 3.0 | 508.8 | 2255.9 |
| `MAX_CONCURRENCY=2`, `SPIN=0`, 2 threads | 1 | 197 | 4.2 | 9.8 | 22.4 |
| | 10 | 399 | 3.8 | 13.9 | 687.4 |
| | 50 | 510 | 3.3 | 13.5 | 3827.4 |

**Findings**
- The default configuration reaches about 970 req/s, 2.9x the single-thread rate (335 req/s), so parallel requests do help.
- Capping concurrency with a semaphore looks good at the median (3 ms) but has a very bad tail (p99 up to 3.8 s) and about 40% lower throughput. A likely explanation is that Python's semaphore is not first-come-first-served, so newly arriving requests can overtake waiting ones and a few requests wait for a long time. We did not measure that mechanism directly. **Rejected.**
- Turning off ONNX Runtime spin-waiting and using 2 threads did not help either. **Rejected.**
- Both settings remain available as environment flags (`INTENT_ROUTER_MAX_CONCURRENCY`, `INTENT_ROUTER_SPIN`), default off, and a test checks that they never change a decision.
- **Reading the 50-thread row (Little's law):** in a closed-loop test, average latency is about concurrency divided by throughput. At 50 threads and 971 req/s that is about 51 ms, so a p95 under 50 ms at 50 simultaneous clients would need roughly twice the capacity.

## 4. Capacity under realistic load (open loop, real `uvicorn main:app`)

Requests arrive at a fixed rate for 10 s regardless of how fast the server answers. Latency is measured from each request's intended send time. The load generator runs on the same machine (it competes with the server for CPU). About 5% of requests are 10,000-character payloads.

| target req/s | achieved | peak in flight | client p50 | p90 | p95 | p99 | router `latency_ms` p50 / p95 |
|---|---|---|---|---|---|---|---|
| 50 | 50 | 4 | 5.6 | 24.6 | **27.6** | 35.6 | 3.8 / 10.1 |
| 100 | 100 | 6 | 7.3 | 22.9 | **27.6** | 34.0 | 4.0 / 10.9 |
| 200 | 200 | 12 | 8.7 | 25.5 | **28.9** | 35.0 | 5.1 / 9.0 |
| 400 | 400 | 29 | 15.3 | 38.2 | **44.6** | 55.0 | 7.0 / 14.5 |

**Result:** client p95 stays under 50 ms up to at least 400 req/s on this machine, with p99 under 50 ms up to 200 req/s. We did not test above 400 req/s, so the true ceiling is higher.

**Closed loop, real server, 50 clients** (`load_test.py`): each client sends its next request as soon as the previous answer arrives.

| concurrency | req/s | client p50 | p90 | p95 | p99 | router `latency_ms` p50 / p95 |
|---|---|---|---|---|---|---|
| 1 | 197 | 4.3 | 6.4 | 12.5 | 14.8 | 2.6 / 5.3 |
| 10 | 490 | 19.8 | 25.8 | 27.5 | 31.0 | 6.7 / 13.7 |
| 50 | 526 | 93.2 | 105.7 | 109.9 | 116.6 | **8.7 / 20.0** |

The same web stack with no model (`--baseline`) sustains 2,098 req/s at 50 clients (client p95 41.2 ms), so the stack and the load generator are not the limit; the model's compute is.

**How to read the 50-client row** (three different latencies):
1. **Router execution time** (the `latency_ms` field of every response, which is what the ticket's "median execution time < 25 ms, p95 < 50 ms" budget describes): at 50 concurrent clients, p50 **8.7 ms** and p95 **20.0 ms**. This meets the budget.
2. **End-to-end latency seen by a client** at 50 clients that keep the server saturated: p95 **109.9 ms**. This is queueing, not slow requests: by Little's law, average latency is about concurrency divided by throughput, and 50 / 526 req/s is about 95 ms. Getting this under 50 ms needs about twice the capacity (INT8 or a second worker process).
3. **End-to-end latency under realistic arrival rates** (open loop, table above): p95 27.6 to 44.6 ms from 50 to 400 req/s.

**Memory:** peak RSS of the whole API process (all Cortex modules loaded) was 219 MB in the closed-loop run and 209 MB in the open-loop run, under the 250 MB limit.

## 5. Where the time goes and memory (`profile_cprofile.py`, `memory_check.py`)

- In-process latency over 2,000 calls (no HTTP): p50 2.30 ms, p90 2.86 ms, p95 3.87 ms, p99 11.04 ms (the p99 comes from the 10,000-character payloads).
- cProfile: ONNX Runtime `run` takes about 88% of the time, tokenizing about 9%, softmax, sorting and rounding under 1% together. The model forward pass is the cost; there is nothing worth optimizing in the Python code around it.
- Memory over 5,000 requests: Python allocations grew by 36 KB and RSS by 0.3 MB (190 MB total for the router process), verdict PASS (thresholds: 512 KB and 10 MB).

## 6. Decision

Production configuration: FP32 model, max_len 64, 4 intra-op threads, batch size 1, no concurrency cap, spin-waiting on, T = 2.0. It meets median under 25 ms and p95 under 50 ms for the router's execution time (in-process p95 3.87 ms; `latency_ms` p95 20.0 ms at 50 concurrent HTTP clients), end-to-end p95 under 50 ms up to 400 req/s of open-loop traffic (27.6 to 44.6 ms), and the 250 MB memory bound (209 to 219 MB). It does **not** keep end-to-end p95 under 50 ms when 50 clients saturate the server (109.9 ms).

Follow-up candidates if end-to-end p95 under 50 ms is required with 50 saturating clients: INT8 (about 2x faster per request, 4x smaller; needs T re-fitted and a repeatable tail measurement) and/or a second worker process (about 2x capacity, but each worker holds the model, so memory per host roughly doubles).

## 7. Limitations

- One machine, one run of each configuration. Run-to-run noise is visible (for example E3's typical latency is lower than E1's, which is not a real effect), and the in-process results depend on the machine state: an earlier run on an unstable machine gave 157 req/s at 50 threads, the repeat gave 970 req/s. The numbers above are from the stable repeat.
- The load generator shares the CPU with the server. With the first load generator (httpx) a no-model server collapsed at 50 clients (p95 1.4 s); with the final one (aiohttp) the same no-model server sustains 2,098 req/s, so the earlier numbers were a harness artifact and are not used.
- Accuracy is measured on only 30 clean validation queries; one query is 3.3 percentage points.
- The 4-intent model has not been evaluated on long inputs; truncation to 64 tokens bounds latency but not accuracy.

## 8. Reproduce

```
python api/modules/intent_router/profiling/bench_experiments.py
python api/modules/intent_router/profiling/load_test.py --inprocess
python api/modules/intent_router/profiling/load_test.py --inprocess --env INTENT_ROUTER_MAX_CONCURRENCY=2
python api/modules/intent_router/profiling/load_test.py --inprocess --env INTENT_ROUTER_MAX_CONCURRENCY=2 --env INTENT_ROUTER_SPIN=0 --threads 2
python api/modules/intent_router/profiling/load_test.py --rates 50 100 200 400
python api/modules/intent_router/profiling/load_test.py
python api/modules/intent_router/profiling/load_test.py --baseline
python api/modules/intent_router/profiling/profile_cprofile.py
python api/modules/intent_router/profiling/memory_check.py
```
