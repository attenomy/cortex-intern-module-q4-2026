# Load test results (inprocess)

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

settings: INTENT_ROUTER_THREADS=1 | 2000 requests per level | ~5% of requests are 10,000-character payloads | all times in ms

| concurrency | req/s | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |
|---|---|---|---|---|---|---|---|---|
| 1 | 66 | 9.6 | 28.1 | 36.1 | 94.7 | 9.6 | 36.0 | 0 |
| 10 | 588 | 11.5 | 36.4 | 47.7 | 82.3 | 11.5 | 47.7 | 0 |
| 50 | 946 | 35.8 | 88.4 | 118.7 | 179.9 | 35.7 | 118.7 | 0 |
