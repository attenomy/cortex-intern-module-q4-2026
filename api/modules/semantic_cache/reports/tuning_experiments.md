# CTX-003 Day 14 - Performance and Tuning Experiments

- Run ID: `1c2b72f1e5764ffda92c1de09920da7f`
- UTC timestamp: `2026-11-05T01:34:25.345415+00:00`
- Workload: isolated Redis namespace; exact and semantic cache paths

## 1. Similarity threshold experiments

| Threshold | Hits / 30 | Hit rate | Median (ms) | P95 (ms) |
|---:|---:|---:|---:|---:|
| 0.7 | 30/30 | 100.0% | 9.535 | 11.311 |
| 0.75 | 30/30 | 100.0% | 8.719 | 11.459 |
| 0.8 | 0/30 | 0.0% | 9.411 | 11.033 |
| 0.85 | 0/30 | 0.0% | 9.619 | 11.316 |
| 0.9 | 0/30 | 0.0% | 9.814 | 10.858 |
| 0.95 | 0/30 | 0.0% | 9.746 | 11.247 |

Semantic baseline similarity: `0.785749`

## 2. Concurrent exact-hit load tests

| Workers | Requests | Throughput (req/s) | Median (ms) | P95 (ms) |
|---:|---:|---:|---:|---:|
| 1 | 100 | 2130.32 | 0.42 | 0.713 |
| 4 | 400 | 3143.09 | 1.12 | 1.985 |
| 8 | 800 | 3157.79 | 2.216 | 4.458 |
| 16 | 1600 | 3172.68 | 4.382 | 9.329 |

## 3. CPU latency SLA

Target: median <25 ms and p95 <50 ms.

- 1 workers: median `0.42 ms`, p95 `0.713 ms` - PASS
- 4 workers: median `1.12 ms`, p95 `1.985 ms` - PASS
- 8 workers: median `2.216 ms`, p95 `4.458 ms` - PASS
- 16 workers: median `4.382 ms`, p95 `9.329 ms` - PASS

## 4. cProfile

- Requests: 1000
- Median: 0.507 ms
- P95: 0.633 ms
- Detailed profile: `../reports/day14_cprofile.txt`

## 5. tracemalloc - 5,000 requests

- Before: 0 bytes
- After GC: 58 bytes
- Net growth: 58 bytes
- Peak traced memory: 76855 bytes

Interpretation: net Python heap growth is measured after garbage collection. This is evidence for this workload, not proof of zero memory leaks.

## 6. Scope and limitations

- Thresholds were varied; the production threshold was not changed.
- Concurrency tests used exact cache hits.
- Semantic lookup was measured separately.
- Redis vector quantization and VSIM candidate count were not changed.
- Results apply to this machine, Redis instance, model and workload.

## 7. Batch-size tuning

- Device: CPU
- Queries per trial: 96
- Trials per batch size: 3
- Model: sentence-transformers/all-MiniLM-L6-v2

| Batch size | Median total (ms) | Per query (ms) | Throughput (queries/s) |
|---:|---:|---:|---:|
| 1 | 491.415 | 5.119 | 195.35 |
| 4 | 409.849 | 4.269 | 234.23 |
| 8 | 227.998 | 2.375 | 421.06 |
| 16 | 194.113 | 2.022 | 494.56 |
| 32 | 172.822 | 1.800 | 555.49 |

Interpretation: Batch size 32 achieved the best bulk throughput,
approximately 2.84x the throughput of batch size 1.

Limitation: This is a direct model encoding benchmark. It does not
demonstrate improved single-request production lookup latency because
production request batching was not implemented.

Detailed results: `day14_batch_size_results.json`
Report: `day14_batch_size_results.md`

## 8. Quantization experiment

- Device: CPU
- Representation: symmetric int8 simulation
- Vector count: 8
- Dimensions: 384

| Metric | Result |
|---|---:|
| Float32 storage | 12,288 bytes |
| Int8 storage | 3,072 bytes |
| Storage reduction | 75.0% |
| Maximum cosine drift | 0.00146917 |
| Mean cosine drift | 0.00035327 |
| P95 cosine drift | 0.00114801 |
| Minimum restored vector norm | 0.99949092 |

Interpretation: The in-memory int8 simulation reduced vector storage
by 75%, with small observed cosine-similarity drift.

Limitation: This experiment did not reconfigure or benchmark Redis
native VSET int8 quantization. The production Redis index remains unchanged.

Detailed results: `day14_quantization_results.json`
Report: `day14_quantization_results.md`

## 9. Semantic lookup concurrency profiling

Workload: CPU semantic lookup using an isolated Redis namespace.
Stored query: "How can I reset my account password?"
Test query: "What steps should I take to change my account password?"
Threshold: 0.70
Requests per worker: 20

| Workers | Requests | Hits | Median (ms) | P95 (ms) | Throughput (req/s) |
|---:|---:|---:|---:|---:|---:|
| 1 | 20 | 20 | 10.650 | 14.963 | 84.47 |
| 4 | 80 | 80 | 104.851 | 130.431 | 38.58 |
| 8 | 160 | 160 | 176.297 | 280.231 | 44.43 |
| 16 | 320 | 320 | 236.168 | 555.633 | 52.85 |

All tested semantic requests returned cache hits. However, the
semantic lookup latency target was not met at 4, 8, or 16 workers.

### PyTorch intra-op thread tuning

Comparative p95 latency (ms):

| Workers | Default (6 threads) | 1 thread | 2 threads | 4 threads |
|---:|---:|---:|---:|---:|
| 1 | 14.963 | 27.575 | 12.357 | 30.829 |
| 4 | 130.431 | 66.049 | 52.240 | 124.194 |
| 8 | 280.231 | 303.439 | 133.695 | 317.898 |
| 16 | 555.633 | 562.782 | 673.637 | 626.431 |

The 2-thread experiment had the best p95 among the tested configurations
at 1, 4, and 8 workers, but no configuration met the strict p95 <50 ms
target at 16 workers. These are individual experiment runs and require
repeatability testing before selecting a production configuration.

Detailed results:
- `day14_semantic_concurrency.json`
- `day14_semantic_concurrency_torch1.json`
- `day14_semantic_concurrency_torch2.json`
- `day14_semantic_concurrency_torch4.json`

## 10. Updated conclusions and limitations

- Six similarity thresholds were tested.
- Five model batch sizes were tested.
- Symmetric int8 quantization was simulated in memory.
- Exact-hit concurrency passed the median and p95 targets at all tested
  worker counts.
- Semantic lookup concurrency failed the p95 target under higher
  concurrency. CPU embedding latency is a major contributor.
- Sequential cProfile and a 5,000-request tracemalloc experiment were
  completed.
- The 58-byte net traced-memory growth after garbage collection is
  encouraging for this workload, but does not prove zero memory leaks.
- Native Redis quantization and candidate-count tuning were not tested.
- Results are specific to this machine, model, Redis instance and workloads.
