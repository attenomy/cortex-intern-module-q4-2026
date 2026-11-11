# CTX-003 - Diagnostic Error Analysis

## 1. Executive Summary

Day 14 profiling identified CPU embedding inference as the primary bottleneck in concurrent semantic cache lookups.

The exact-query fast path meets the latency targets in the tested workload. Semantic lookups meet the target at one worker but fail under higher concurrency.

## 2. Performance Acceptance Criteria

| Metric | Target |
|---|---:|
| Median latency | < 25 ms |
| P95 latency | < 50 ms |
| Execution device | CPU |

Both limits are strict.

## 3. Semantic Concurrency Results

| Workers | Requests | Median (ms) | P95 (ms) | SLA |
|---:|---:|---:|---:|---|
| 1 | 20 | 10.650 | 14.963 | PASS |
| 4 | 80 | 104.851 | 130.431 | FAIL |
| 8 | 160 | 176.297 | 280.231 | FAIL |
| 16 | 320 | 236.168 | 555.633 | FAIL |

All tested semantic requests returned cache hits.

## 4. Root Cause Analysis

### CPU embedding versus Redis latency

| Workers | Embedding median (ms) | Redis median (ms) |
|---:|---:|---:|
| 1 | 6.894 | 3.255 |
| 4 | 90.285 | 11.084 |
| 8 | 159.791 | 12.073 |
| 16 | 215.814 | 20.152 |

CPU embedding inference is the primary bottleneck. Redis latency also increases under load but contributes less than embedding inference.

### PyTorch thread tuning

Comparative P95 latency (ms):

| Workers | Default 6 threads | 1 thread | 2 threads | 4 threads |
|---:|---:|---:|---:|---:|
| 1 | 14.963 | 27.575 | 12.357 | 30.829 |
| 4 | 130.431 | 66.049 | 52.240 | 124.194 |
| 8 | 280.231 | 303.439 | 133.695 | 317.898 |
| 16 | 555.633 | 562.782 | 673.637 | 626.431 |

Two threads performed best at 1, 4 and 8 workers among the tested configurations. No tested configuration met the P95 target at 16 workers.

These are individual experimental runs and require repeatability testing.

## 5. Exact-Query Fast Path

| Workers | Requests | Median (ms) | P95 (ms) | SLA |
|---:|---:|---:|---:|---|
| 1 | 100 | 0.420 | 0.713 | PASS |
| 4 | 400 | 1.120 | 1.985 | PASS |
| 8 | 800 | 2.216 | 4.458 | PASS |
| 16 | 1600 | 4.382 | 9.329 | PASS |

The exact-query path avoids embedding inference and meets the latency target in this workload. This does not establish semantic lookup SLA compliance.

## 6. Additional Tuning Findings

### Batch-size experiment

Batch sizes 1, 4, 8, 16 and 32 were tested using 96 queries and three trials.

Batch size 32 achieved 555.49 queries/second compared with 195.35 for batch size 1.

This was a direct model encoding benchmark, not production request micro-batching.

### Quantization experiment

An in-memory symmetric int8 simulation reported:

- Float32 storage: 12,288 bytes.
- Int8 storage: 3,072 bytes.
- Storage reduction: 75%.
- Maximum cosine similarity drift: 0.00146917.
- Mean cosine similarity drift: 0.00035327.

Redis native VSET quantization was not changed or benchmarked.

### Memory profiling

The 5,000-request tracemalloc experiment reported:

- Initial traced memory: 0 bytes.
- Memory after garbage collection: 58 bytes.
- Net growth: 58 bytes.
- Peak traced memory: 76,855 bytes.

This is evidence for the tested workload, not proof of zero memory leaks.

## 7. Recommended Corrective Actions

1. Evaluate bounded embedding inference concurrency.
2. Evaluate request micro-batching.
3. Repeat concurrency tests to confirm improvements.
4. Evaluate ONNX Runtime or another optimized CPU inference path.
5. Profile embedding and Redis stages independently.
6. Test representative mixed exact-hit, semantic-hit and cache-miss traffic.

Do not change the production Redis index without a separately validated migration.

## 8. Known Limitations

- Results depend on the test machine, model, Redis instance and workload.
- Thread-count comparisons are individual runs.
- Semantic concurrency used one stored query and one related query.
- Production micro-batching was not implemented.
- Native Redis int8 quantization was not benchmarked.
- VSIM candidate-count tuning was not performed.
- Memory profiling does not formally prove the absence of leaks.

## 9. Final SLA Status

| Workload | Result |
|---|---|
| Exact-query path, 1-16 workers | PASS |
| Semantic lookup, 1 worker | PASS |
| Semantic lookup, 4 workers | FAIL |
| Semantic lookup, 8 workers | FAIL |
| Semantic lookup, 16 workers | FAIL |

Overall conclusion:

The core semantic cache implementation is functional, and the exact lookup optimization performs well. However, the high-concurrency semantic CPU latency requirement remains an open performance issue.

The limitation is documented transparently, with measured evidence and recommended corrective actions.
