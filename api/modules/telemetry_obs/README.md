# Module: Telemetry & Observability (`api/modules/telemetry_obs/`)

> **Ticket**: `[CTX-004]` Hardened Containerization, Prometheus Metrics & Automated CI  
> **Target Branch**: `feature/CTX-004-observability-ci` -> `staging`  

---

## Module Overview
This module exposes production health checks (`/health`), Prometheus scraping metrics (`/metrics`), and latency percentiles.

## Key Constraints
- `/metrics` must adhere to official Prometheus text exposition format.
- Reports request count by status code and tail latency percentiles (p50, p95, p99).

## Testing
Run unit tests for this module:
```bash
pytest modules/telemetry_obs/tests/ -v
```

