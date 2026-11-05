# Load test results (http)

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

settings: defaults | 2000 requests per level | ~5% of requests are 10,000-character payloads | all times in ms

| concurrency | req/s | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |
|---|---|---|---|---|---|---|---|---|
| 1 | 197 | 4.3 | 6.4 | 12.5 | 14.8 | 2.6 | 5.3 | 0 |
| 10 | 490 | 19.8 | 25.8 | 27.5 | 31.0 | 6.7 | 13.7 | 0 |
| 50 | 526 | 93.2 | 105.7 | 109.9 | 116.6 | 8.7 | 20.0 | 0 |

Server peak RSS (process tree): 219 MB
