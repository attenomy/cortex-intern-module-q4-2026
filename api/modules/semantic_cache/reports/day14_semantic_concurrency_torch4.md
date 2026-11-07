# CTX-003 Day 14 — CPU Semantic Concurrency

- Run ID: `a9897c4efb764aa58bb9e66f758e54d3`
- Timestamp UTC: `2026-11-05T02:22:49.642606+00:00`
- Model device: `cpu`
- Similarity threshold: `0.7`
- Baseline similarity score: `0.785749`

| Workers | Requests | Hits | Misses | Median (ms) | P95 (ms) | Throughput (req/s) | SLA |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 20 | 20 | 0 | 15.974 | 30.829 | 54.29 | PASS |
| 4 | 80 | 80 | 0 | 72.287 | 124.194 | 50.62 | FAIL |
| 8 | 160 | 160 | 0 | 121.126 | 317.898 | 46.65 | FAIL |
| 16 | 320 | 320 | 0 | 236.337 | 626.431 | 50.15 | FAIL |

## Profiling

Concurrent latency was measured using the async worker harness.
Sequential cProfile results are available in day14_cprofile.txt from the original benchmark.

## Limitations

- This measures semantic lookups with CPU embedding and Redis VSIM.
- The workload uses one stored query and one semantically related query.
- Twenty requests were run per worker.
- A miss is counted separately; it is not silently treated as a hit.
- Results apply to this machine and this workload.
