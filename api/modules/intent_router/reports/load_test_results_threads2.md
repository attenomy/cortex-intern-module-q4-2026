# Load test results (http)

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

settings: INTENT_ROUTER_THREADS=2 | 60 s per level | ~5% of requests are 10,000-character payloads | all times in ms

| concurrency | req/s | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |
|---|---|---|---|---|---|---|---|---|
| 50 | 242 | 45.3 | 54.0 | 57.7 | 251.4 | 7.7 | 17.1 | 26 |

Server peak RSS (process tree): 194 MB
