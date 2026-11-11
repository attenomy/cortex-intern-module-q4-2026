# CTX-003 Day 14 - Batch Size Tuning

- Device: cpu
- PyTorch intra-op threads: 6
- Queries per trial: 96
- Trials per batch size: 3

| Batch size | Median total (ms) | Per query (ms) | Throughput (queries/s) |
|---:|---:|---:|---:|
| 1 | 491.415 | 5.119 | 195.35 |
| 4 | 409.849 | 4.269 | 234.23 |
| 8 | 227.998 | 2.375 | 421.06 |
| 16 | 194.113 | 2.022 | 494.56 |
| 32 | 172.822 | 1.8 | 555.49 |
