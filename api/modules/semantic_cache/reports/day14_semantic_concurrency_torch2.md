# CTX-003 Day 14 — CPU Semantic Concurrency

- Run ID: `7a79fd590542465f801a46db3b1a78f9`
- Timestamp UTC: `2026-11-05T02:20:36.521920+00:00`
- Model device: `cpu`
- Similarity threshold: `0.7`
- Baseline similarity score: `0.785749`

| Workers | Requests | Hits | Misses | Median (ms) | P95 (ms) | Throughput (req/s) | SLA |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 20 | 20 | 0 | 10.727 | 12.357 | 93.35 | PASS |
| 4 | 80 | 80 | 0 | 45.752 | 52.24 | 88.2 | FAIL |
| 8 | 160 | 160 | 0 | 114.409 | 133.695 | 70.15 | FAIL |
| 16 | 320 | 320 | 0 | 306.162 | 673.637 | 45.74 | FAIL |

## Profiling

Concurrent latency was measured using the async worker harness.
Sequential cProfile results are available in day14_cprofile.txt from the original benchmark.

## Limitations

- This measures semantic lookups with CPU embedding and Redis VSIM.
- The workload uses one stored query and one semantically related query.
- Twenty requests were run per worker.
- A miss is counted separately; it is not silently treated as a hit.
- Results apply to this machine and this workload.
