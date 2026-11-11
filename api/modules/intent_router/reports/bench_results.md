# Benchmark results

Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`

Temperature T = 2.0. 'typical' = dataset queries, 'worst-case' = one 10,000-character payload. Batch rows report latency per CALL.

| ID | model | threads | max_len | batch | typical p50 / p95 (ms) | worst-case p50 / p95 (ms) | items/s | size MB | clean acc | fallback |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | fp32 | 4 | 64 | 1 | 2.90 / 4.04 | 12.53 / 15.20 | 345 | 90 | 0.967 | 0.03 |
| E2 | fp32 | 4 | 128 | 1 | 2.77 / 3.77 | 17.53 / 20.57 | 362 | 90 | 0.967 | 0.03 |
| E3 | fp32 | 4 | 256 | 1 | 2.20 / 2.86 | 25.41 / 29.94 | 454 | 90 | 0.967 | 0.03 |
| E4 | fp32 | 4 | 64 | 4 | 6.70 / 8.75 | 27.73 / 38.15 | 597 | 90 | 0.967 | 0.03 |
| E5 | fp32 | 4 | 64 | 16 | 24.63 / 31.90 | 93.25 / 116.08 | 650 | 90 | 0.967 | 0.03 |
| E6 | int8 | 4 | 64 | 1 | 1.36 / 1.76 | 13.36 / 29.00 | 734 | 23 | 0.967 | 0.07 |
| E7 | int8 | 4 | 256 | 1 | 3.56 / 7.54 | 19.22 / 68.91 | 281 | 23 | 0.967 | 0.07 |
| E8 | fp32 | 1 | 64 | 1 | 6.00 / 10.35 | 25.75 / 37.65 | 167 | 90 | 0.967 | 0.03 |
| E9 | fp32 | 2 | 64 | 1 | 3.17 / 4.13 | 15.14 / 15.72 | 316 | 90 | 0.967 | 0.03 |
