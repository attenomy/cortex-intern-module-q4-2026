# Load test results (baseline)

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

settings: defaults | 2000 requests per level | ~5% of requests are 10,000-character payloads | all times in ms

| concurrency | req/s | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |
|---|---|---|---|---|---|---|---|---|
| 1 | 1085 | 0.8 | 1.2 | 1.4 | 1.6 | - | - | 0 |
| 10 | 1966 | 4.8 | 5.4 | 5.8 | 13.0 | - | - | 0 |
| 50 | 2098 | 21.0 | 24.7 | 41.2 | 68.7 | - | - | 0 |

Server peak RSS (process tree): 60 MB
