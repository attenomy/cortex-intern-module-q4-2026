# [CTX-004] Prometheus Metrics & Telemetry for Cortex

## 1. Overview

This contribution introduces a Prometheus-based monitoring and observability layer for the Attenomy Cortex API. The objective is to improve service visibility, monitor API behavior, measure request latency, track semantic cache activity, and expose operational metrics in a standardized format.

The implementation integrates Prometheus instrumentation into the existing FastAPI application through dedicated telemetry services, HTTP middleware, and an API endpoint.

This enables developers and operators to inspect application-level metrics and establish a foundation for future monitoring, alerting, performance analysis, and production observability.

## 2. Objectives

The primary objectives of this implementation are:

- Establish centralized application-level metric collection.
- Monitor incoming HTTP requests and their response latency.
- Track semantic cache hit activity.
- Monitor application lifecycle activity.
- Provide a standardized Prometheus metrics endpoint.
- Maintain compatibility with the existing Cortex application architecture.
- Ensure telemetry functionality through automated tests.
- Keep monitoring independent of the main application request-handling logic wherever possible.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core implementation |
| FastAPI | API framework |
| Prometheus Client | Metric registration and collection |
| Starlette Middleware | HTTP request instrumentation |
| Pytest | Automated testing |
| Ruff | Code quality and lint validation |

## 4. Architecture & Implementation

The telemetry implementation is organized into a dedicated module:

`api/modules/telemetry_obs/`

### 4.1 Prometheus Metric Service

Implemented a centralized telemetry service responsible for defining and managing application metrics.

Responsibilities include:

- Defining Prometheus counters, gauges, and histograms.
- Registering application metrics.
- Providing helper functions for updating metrics.
- Tracking service uptime.
- Maintaining metric collection independently from API business logic.

### 4.2 HTTP Request Monitoring Middleware

Introduced custom middleware to instrument incoming HTTP requests.

The middleware records:

- Total HTTP requests received.
- Request processing duration.
- HTTP response status.
- Request route information where available.

This provides visibility into API traffic and request-processing behavior.

The `/metrics` endpoint is excluded from request instrumentation to avoid monitoring scrapes inflating application request metrics.

### 4.3 Request Latency Monitoring

Implemented a Prometheus histogram to observe HTTP request processing time.

Latency observations are collected in seconds using predefined histogram buckets.

This allows future monitoring systems to calculate latency distributions and derive percentile estimates from collected histogram data.

### 4.4 Semantic Cache Monitoring

Integrated semantic cache hit tracking with the existing semantic caching service.

The implementation records cache-hit events when matching cached responses are retrieved.

This provides a metric for understanding cache utilization and evaluating the effectiveness of semantic caching.

### 4.5 Application Lifecycle Monitoring

Integrated application lifecycle instrumentation into the semantic cache application lifespan.

The Prometheus gauge tracks active semantic cache application lifespans through startup and shutdown events.

Lifecycle helper functions update the gauge when the application starts and stops.

### 4.6 Prometheus Metrics API

Exposed a dedicated `/metrics` endpoint through the telemetry router.

The endpoint returns metrics in Prometheus text exposition format, allowing compatible monitoring systems to scrape the application's metrics.

**Endpoint:** `GET /metrics`

**Verified HTTP status:** `200 OK`

**Response format:** Prometheus text exposition format.

## 5. Metrics Implemented

The following custom metrics were introduced:

| Metric Name | Type | Description |
|---|---|---|
| `cortex_requests_total` | Counter | Total HTTP requests received by Cortex |
| `cortex_request_latency_seconds` | Histogram | Observed HTTP request latency in seconds |
| `cortex_cache_hits_total` | Counter | Total semantic cache hits |
| `cortex_active_workers` | Gauge | Number of active semantic cache application lifespans |
| `cortex_uptime_seconds` | Gauge | Total service uptime in seconds |

### Metric Types

- **Counter:** Tracks cumulative events, such as incoming requests and cache hits.
- **Histogram:** Records observations such as HTTP request duration across predefined buckets.
- **Gauge:** Tracks values that can increase or decrease, such as active application lifespans and uptime.

## 6. API Verification – `/metrics`

The Prometheus endpoint was verified using FastAPI's TestClient.

**Request:**

`GET /metrics`

**Actual response status:** `200 OK`

**Content type:** Prometheus text exposition format.

### Sample Metrics Response

```text
# HELP cortex_requests_total Total HTTP requests received by Cortex
# TYPE cortex_requests_total counter

# HELP cortex_request_latency_seconds Observed HTTP request latency in seconds
# TYPE cortex_request_latency_seconds histogram

cortex_request_latency_seconds_count 0.0
cortex_request_latency_seconds_sum 0.0

# HELP cortex_cache_hits_total Total semantic cache hits
# TYPE cortex_cache_hits_total counter
cortex_cache_hits_total 0.0

# HELP cortex_active_workers Number of active semantic cache application lifespans
# TYPE cortex_active_workers gauge
cortex_active_workers 0.0

# HELP cortex_uptime_seconds Total service uptime in seconds
# TYPE cortex_uptime_seconds gauge
cortex_uptime_seconds 0.16207075119018555
```

*Note: The displayed values are from an actual fresh TestClient metrics scrape. Counters and gauges can initially report zero when no corresponding activity has occurred in that process.*

## 7. Testing & Validation

Automated tests were executed for both telemetry functionality and semantic cache functionality to verify compatibility and prevent regressions.

### 7.1 Pytest Execution

**Command:**

```bash
py -m pytest modules\telemetry_obs\tests modules\semantic_cache\tests -v
```

**Test Results:**

```text
41 passed
0 failed
Execution time: 5.65 seconds
```

The test execution covered telemetry and semantic cache test suites, including the application lifecycle test.

### 7.2 Ruff Code Quality Validation

**Command:**

```bash
py -m ruff check modules\telemetry_obs modules\semantic_cache\router.py modules\semantic_cache\service.py main.py
```

**Result:**

```text
All checks passed!
```

No Ruff lint errors were reported for the checked files.

### 7.3 Validation Summary

- [x] Prometheus metric definitions verified.
- [x] HTTP request monitoring implemented.
- [x] Request latency histogram implemented.
- [x] Semantic cache hit tracking integrated.
- [x] Application lifecycle gauge integrated.
- [x] `/metrics` endpoint verified with HTTP 200.
- [x] Telemetry tests executed successfully.
- [x] Semantic cache regression tests passed.
- [x] Ruff validation completed successfully.

## 8. Files Changed

The following files were modified or added as part of CTX-004:

### Application Integration
- `api/main.py` – Integrated telemetry middleware and router into the FastAPI application.

### Semantic Cache Integration
- `api/modules/semantic_cache/router.py` – Integrated application lifecycle metric updates.
- `api/modules/semantic_cache/service.py` – Integrated semantic cache hit instrumentation.
- `api/modules/semantic_cache/tests/test_lifecycle.py` – Added lifecycle metric validation.

### Telemetry Module
- `api/modules/telemetry_obs/__init__.py` – Telemetry module initialization.
- `api/modules/telemetry_obs/middleware.py` – HTTP request monitoring middleware.
- `api/modules/telemetry_obs/router.py` – Health and Prometheus metrics endpoints.
- `api/modules/telemetry_obs/service.py` – Prometheus metric definitions and helper functions.
- `api/modules/telemetry_obs/tests/test_telemetry.py` – Telemetry functionality tests.

### Dependencies
- `api/requirements.txt` – Added the Prometheus client dependency.

**Total files changed:** 10  
**Modified files:** 8  
**Added files:** 2  
**Deleted files:** 0

## 9. Design Considerations

The implementation follows a modular approach to keep telemetry separate from the core business logic.

Key considerations:

- Dedicated telemetry module for centralized metric management.
- Middleware-based instrumentation to reduce repetitive monitoring logic.
- Prometheus standard metric types for compatibility with monitoring tools.
- Lifecycle-aware gauge updates.
- Automated tests to validate instrumentation behavior.
- Exclusion of the metrics scrape endpoint from request counting to avoid self-instrumentation noise.

## 10. Performance Benchmarking

The current submission verifies metric collection, endpoint functionality, and automated test execution.

Dedicated p50/p95 latency benchmarks, concurrent-load measurements, and resource-overhead measurements have not yet been collected. These are therefore not reported as measured performance results.

## 11. Branch & Pull Request Information

- **Ticket ID:** CTX-004 – Prometheus Metrics & Telemetry
- **Feature Branch:** `feature/CTX-004-prometheus-telemetry`
- **Target Branch:** `staging`
- **Pull Request:** https://github.com/attenomy/cortex-intern-module-q4-2026/pull/12

The PR base branch was updated from `main` to `staging` to ensure the comparison contains only the intended feature changes.

## 12. Video Walkthrough

**60–90 Second Implementation Walkthrough:**

https://drive.google.com/file/d/1hxLwuhpHbtage4Nmfr_21Cqbl1qNEYos/view

The walkthrough demonstrates the telemetry implementation, Prometheus metrics endpoint, and test verification.

## 13. Final Verification Checklist

- [x] Prometheus client integrated.
- [x] Request monitoring middleware implemented.
- [x] HTTP latency histogram configured.
- [x] Semantic cache hit counter integrated.
- [x] Application lifecycle gauge implemented.
- [x] Prometheus `/metrics` endpoint operational.
- [x] Automated tests: 41 passed, 0 failed.
- [x] Ruff checks passed.
- [x] Changes reviewed against the `staging` branch.
- [x] No deleted files in the PR comparison.
- [ ] Replace the video placeholder with the actual recording URL.

## 14. Conclusion

The CTX-004 implementation successfully introduces a structured Prometheus-based observability layer into the Attenomy Cortex API.

By combining HTTP request instrumentation, latency monitoring, semantic cache metrics, application lifecycle tracking, and a standardized metrics endpoint, the implementation establishes a foundation for monitoring application behavior and improving operational visibility.

The changes have been validated through 41 passing automated tests, successful Ruff checks, and direct verification of the Prometheus `/metrics` endpoint.

**Status:** Implementation and local validation completed. Ready for PR review.
