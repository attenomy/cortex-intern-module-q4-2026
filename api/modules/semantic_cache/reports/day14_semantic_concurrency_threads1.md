# CTX-003 Day 14 — CPU Semantic Concurrency

- Run ID: `3e3b31d94c804061ab2b1aa6050188bf`
- Timestamp UTC: `2026-11-05T02:14:37.627610+00:00`
- Model device: `cpu`
- Similarity threshold: `0.7`
- Baseline similarity score: `0.785749`

| Workers | Requests | Hits | Misses | Median (ms) | P95 (ms) | Throughput (req/s) | SLA |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 20 | 20 | 0 | 18.92 | 27.863 | 50.33 | PASS |
| 4 | 80 | 80 | 0 | 96.065 | 147.025 | 41.39 | FAIL |
| 8 | 160 | 160 | 0 | 225.551 | 297.349 | 40.97 | FAIL |
| 16 | 320 | 320 | 0 | 365.634 | 642.304 | 40.12 | FAIL |

## Profiling

Concurrent latency was measured using the async worker harness.
Sequential cProfile results are available in day14_cprofile.txt from the original benchmark.

## Limitations

- This measures semantic lookups with CPU embedding and Redis VSIM.
- The workload uses one stored query and one semantically related query.
- Twenty requests were run per worker.
- A miss is counted separately; it is not silently treated as a hit.
- Results apply to this machine and this workload.
