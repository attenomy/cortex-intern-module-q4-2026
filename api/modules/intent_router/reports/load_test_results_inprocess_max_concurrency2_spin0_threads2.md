# Load test results (inprocess)

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

settings: INTENT_ROUTER_MAX_CONCURRENCY=2, INTENT_ROUTER_SPIN=0, INTENT_ROUTER_THREADS=2 | 2000 requests per level | ~5% of requests are 10,000-character payloads | all times in ms

| concurrency | req/s | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |
|---|---|---|---|---|---|---|---|---|
| 1 | 197 | 4.2 | 7.1 | 9.8 | 22.4 | 4.1 | 9.8 | 0 |
| 10 | 399 | 3.8 | 8.3 | 13.9 | 687.4 | 3.8 | 13.8 | 0 |
| 50 | 510 | 3.3 | 6.2 | 13.5 | 3827.4 | 3.3 | 13.5 | 0 |
