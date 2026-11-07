# CTX-003 Day 14 - Quantization Experiment

- Device: cpu
- Representation: symmetric int8 simulation
- Vector count: 8
- Dimensions: 384

| Metric | Result |
|---|---:|
| Float32 storage | 12288 bytes |
| Int8 storage | 3072 bytes |
| Storage reduction | 75.0% |
| Maximum cosine drift | 0.00146917 |
| Mean cosine drift | 0.00035327 |
| P95 cosine drift | 0.00114801 |
| Minimum restored vector norm | 0.99949092 |

**Limitation:** This is an in-memory symmetric int8 quantization simulation.
It does not reconfigure or benchmark Redis VSET's native int8 quantization.
