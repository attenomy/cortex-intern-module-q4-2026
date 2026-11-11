# Load test results (http, open-loop)

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

settings: defaults | 10 s per rate | ~5% of requests are 10,000-character payloads | all times in ms

| target req/s | achieved req/s | peak in flight | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |
|---|---|---|---|---|---|---|---|---|---|
| 50 | 50 | 4 | 5.6 | 24.6 | 27.6 | 35.6 | 3.8 | 10.1 | 0 |
| 100 | 100 | 6 | 7.3 | 22.9 | 27.6 | 34.0 | 4.0 | 10.9 | 0 |
| 200 | 200 | 12 | 8.7 | 25.5 | 28.9 | 35.0 | 5.1 | 9.0 | 0 |
| 400 | 400 | 29 | 15.3 | 38.2 | 44.6 | 55.0 | 7.0 | 14.5 | 0 |

Server peak RSS (process tree): 209 MB
