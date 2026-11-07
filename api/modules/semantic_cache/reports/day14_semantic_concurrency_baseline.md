# CTX-003 Day 14 - CPU Semantic Concurrency

- Run ID: `b3087b02a22a48d0824ecdbc128bef9e`
- Timestamp UTC: `2026-11-05T02:10:35.901203+00:00`
- Model device: `cpu`
- Similarity threshold: `0.7`
- Baseline similarity score: `0.785749`

| Workers | Requests | Hits | Misses | Median (ms) | P95 (ms) | Throughput (req/s) | SLA |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | 20 | 20 | 0 | 10.65 | 14.963 | 84.47 | PASS |
| 4 | 80 | 80 | 0 | 104.851 | 130.431 | 38.58 | FAIL |
| 8 | 160 | 160 | 0 | 176.297 | 280.231 | 44.43 | FAIL |
| 16 | 320 | 320 | 0 | 236.168 | 555.633 | 52.85 | FAIL |

## Profiling

Concurrent latency was measured using the async worker harness.
Sequential cProfile results are available in day14_cprofile.txt from the original benchmark.

## Limitations

- This measures semantic lookups with CPU embedding and Redis VSIM.
- The workload uses one stored query and one semantically related query.
- Twenty requests were run per worker.
- A miss is counted separately; it is not silently treated as a hit.
- Results apply to this machine and this workload.
