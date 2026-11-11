# Load test results (inprocess)

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

settings: defaults | 2000 requests per level | ~5% of requests are 10,000-character payloads | all times in ms

| concurrency | req/s | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |
|---|---|---|---|---|---|---|---|---|
| 1 | 335 | 2.4 | 3.9 | 6.0 | 12.1 | 2.4 | 6.0 | 0 |
| 10 | 970 | 8.7 | 14.4 | 24.4 | 30.0 | 8.6 | 24.4 | 0 |
| 50 | 971 | 32.0 | 88.9 | 111.8 | 181.6 | 32.0 | 111.8 | 0 |
