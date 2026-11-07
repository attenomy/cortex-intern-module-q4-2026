# Load test results (http)

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

settings: defaults, workers=3 | 60 s per level | ~5% of requests are 10,000-character payloads | all times in ms

| concurrency | req/s | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |
|---|---|---|---|---|---|---|---|---|
| 50 | 502 | 57.4 | 224.5 | 361.3 | 604.0 | 14.8 | 191.1 | 0 |

Server peak RSS (process tree): 656 MB
