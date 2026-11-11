# CTX-003 Day 14 - CPU Semantic Concurrency

- Run ID: `eacfeb83b0b7431f941967c1fff27498`
- Timestamp UTC: `2026-11-05T02:25:23.147742+00:00`
- Model device: `cpu`
- Similarity threshold: `0.7`
- Baseline similarity score: `0.785749`

| Workers | Requests | Hits | Misses | Median (ms) | P95 (ms) | Throughput (req/s) | SLA |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 20 | 20 | 0 | 18.526 | 27.575 | 52.16 | PASS |
| 4 | 80 | 80 | 0 | 41.7 | 66.049 | 83.15 | FAIL |
| 8 | 160 | 160 | 0 | 270.692 | 303.439 | 30.9 | FAIL |
| 16 | 320 | 320 | 0 | 472.221 | 562.782 | 40.3 | FAIL |

## Profiling

Concurrent latency was measured using the async worker harness.
Sequential cProfile results are available in day14_cprofile.txt from the original benchmark.

## Limitations

- This measures semantic lookups with CPU embedding and Redis VSIM.
- The workload uses one stored query and one semantically related query.
- Twenty requests were run per worker.
- A miss is counted separately; it is not silently treated as a hit.
- Results apply to this machine and this workload.
