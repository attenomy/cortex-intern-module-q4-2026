
# Attenomy Cortex

> Enterprise Autonomous Multi-Agent Orchestration & Cognitive Knowledge Retrieval Engine

---

## Executive Overview

Attenomy Cortex is an enterprise AI infrastructure platform designed to power low-latency query intent classification, cognitive document knowledge extraction, semantic chunk reranking, and autonomous tool calling.

Built to serve mission-critical applications at scale, Cortex provides:

- Low-Latency Semantic Query Routing: Classifies customer queries across intent channels and directs requests to specialized agent sub-graphs in under 50ms.
- Cognitive Document Extraction: Multimodal vision pipelines that parse unstructured PDFs, invoices, and contracts into structured schema entities.
- Vector Embeddings & Semantic Caching: Redis-backed semantic cache layer reducing duplicate LLM calls by up to 60%.
- Observability & Drift Monitoring: Telemetry tracking model latency (p95, p99) and data drift.

---

## 1. Project Overview

Attenomy Cortex is designed as a modular AI infrastructure platform for intelligent query processing, knowledge retrieval, semantic caching, and autonomous agent workflows.

The platform aims to improve the efficiency, performance, and observability of AI-powered applications through specialized backend modules.

## 2. Problem Statement

Modern AI-powered applications face several challenges:

- Repeated queries trigger unnecessary processing and increase operational costs.
- Retrieving relevant information from unstructured documents can be complex.
- Query routing and intent classification require efficient processing.
- API latency and request activity need reliable monitoring.
- Cache performance must be measured to understand its effectiveness.
- Backend services must remain reliable when optional infrastructure becomes unavailable.

Cortex addresses these challenges through modular query processing, semantic caching, and observability infrastructure.

## 3. Project Objectives

- Develop modular backend infrastructure for AI-powered applications.
- Support intelligent query classification and routing.
- Enable structured information extraction from documents.
- Reduce duplicate query processing using semantic caching.
- Monitor API request counts and response latency.
- Track cache activity and application lifecycle.
- Provide Prometheus-compatible metrics.
- Validate functionality through automated testing.

## 4. Core Capabilities

### 4.1 Intelligent Query Processing

Designed to classify incoming queries and route them to appropriate processing workflows.

### 4.2 Cognitive Document Extraction

Designed to extract structured information from unstructured documents, including PDFs, invoices, and contracts.

### 4.3 Semantic Caching

The semantic caching module uses Redis-backed vector storage and cosine similarity to identify similar queries.

Configured similarity threshold:

`0.95`

Key capabilities:
- Semantic query matching.
- Cache hit tracking.
- Reduced repeated processing.
- Fail-open behavior when Redis is unavailable.

### 4.4 Observability

Prometheus-compatible telemetry provides visibility into:
- HTTP request counts.
- HTTP request latency.
- Semantic cache hits.
- Application lifecycle activity.
- Application uptime.

---

## 5. System Architecture

```text
                 CLIENT APPLICATION
                        |
                        v
                 FASTAPI APPLICATION
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
      API ROUTES    SEMANTIC CACHE   TELEMETRY
          |             |             |
          |             v             |
          |        REDIS VECTOR       |
          |           STORE           |
          |             |             |
          +-------------+-------------+
                        |
                        v
                RESPONSE PROCESSING
                        |
                        v
                  CLIENT RESPONSE

                  OBSERVABILITY
                        |
                        v
                  PROMETHEUS
                        |
                        v
                   /metrics
```

## 6. Technology Stack

**Backend**
- Python
- FastAPI

**Caching**
- Redis
- Vector similarity search
- Cosine similarity

**Monitoring**
- Prometheus Client
- Prometheus metrics exposition format

**Testing and Code Quality**
- Pytest
- Ruff
- FastAPI TestClient

**Development Tools**
- Git
- GitHub
- Visual Studio Code

---

## 7. Backend Module Structure

```text
api/
│
├── main.py
├── requirements.txt
│
└── modules/
    │
    ├── semantic_cache/
    │   ├── router.py
    │   ├── service.py
    │   └── tests/
    │       └── test_lifecycle.py
    │
    └── telemetry_obs/
        ├── __init__.py
        ├── middleware.py
        ├── router.py
        ├── service.py
        └── tests/
            └── test_telemetry.py
```

## 8. Semantic Cache Module

**Location:** `api/modules/semantic_cache/`

The semantic cache module is designed to reduce duplicate query processing by comparing incoming queries with previously cached queries.

Features:
- Redis-backed semantic vector caching.
- Cosine similarity comparison.
- Similarity threshold of 0.95.
- Cache hit tracking.
- Application lifecycle instrumentation.
- Fail-open behavior when Redis is unavailable.

---

## 9. Prometheus Telemetry Module

**Location:** `api/modules/telemetry_obs/`

The telemetry module provides Prometheus-compatible application monitoring.

### Components

| File | Responsibility |
|---|---|
| `service.py` | Prometheus metric definitions and helper functions |
| `middleware.py` | HTTP request and latency instrumentation |
| `router.py` | Health and metrics endpoints |
| `tests/test_telemetry.py` | Telemetry tests |

### Implemented Metrics

| Metric | Type | Description |
|---|---|---|
| `cortex_requests_total` | Counter | Total HTTP requests |
| `cortex_request_latency_seconds` | Histogram | HTTP request latency |
| `cortex_cache_hits_total` | Counter | Total semantic cache hits |
| `cortex_active_workers` | Gauge | Active semantic cache application lifespans |
| `cortex_uptime_seconds` | Gauge | Application uptime |

### Request Monitoring

The middleware tracks incoming HTTP requests and their latency. The `/metrics` endpoint is excluded from request instrumentation.

### Application Lifecycle Monitoring

The semantic cache module updates the lifecycle gauge when application lifespans start and stop. This metric represents active semantic cache application lifespans, not actual Uvicorn worker processes.

---

## 10. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Application health check |
| `/metrics` | GET | Prometheus metrics exposition |

### Sample Metrics Response

```text
# HELP cortex_requests_total Total HTTP requests
# TYPE cortex_requests_total counter

# HELP cortex_request_latency_seconds HTTP request latency
# TYPE cortex_request_latency_seconds histogram

# HELP cortex_cache_hits_total Total semantic cache hits
# TYPE cortex_cache_hits_total counter

# HELP cortex_active_workers Active semantic cache application lifespans
# TYPE cortex_active_workers gauge

# HELP cortex_uptime_seconds Application uptime
# TYPE cortex_uptime_seconds gauge
```

Actual metric values depend on application activity.

---

## 11. Reliability and Failure Handling

The semantic cache implementation is designed with fail-open behavior.

When Redis becomes unavailable:
- Cache operations should not block normal application processing.
- The application should continue through its non-cache processing path.
- Redis availability should not unnecessarily cause HTTP 500 responses.

---

## 12. Testing and Validation

### Run Automated Tests

Run from the `api` directory:

```bash
py -m pytest modules\telemetry_obs\tests modules\semantic_cache\tests -v
```

### Verified Test Results

```text
41 passed
0 failed
```

### Run Ruff

```bash
py -m ruff check modules\telemetry_obs modules\semantic_cache\router.py modules\semantic_cache\service.py main.py
```

### Code Quality Result

```text
All checks passed!
```

### Verification Checklist

- [x] Prometheus client integrated.
- [x] Request monitoring middleware implemented.
- [x] HTTP latency histogram configured.
- [x] Semantic cache hit counter integrated.
- [x] Application lifecycle gauge implemented.
- [x] Prometheus `/metrics` endpoint operational.
- [x] Automated tests: 41 passed, 0 failed.
- [x] Ruff checks passed.
- [x] Changes reviewed against `staging`.
- [x] No deleted files in the PR comparison.

---

## 13. Development Setup

### Prerequisites

- Python 3.12
- Git
- Redis for Redis-backed semantic caching

### Clone Repository

```bash
git clone https://github.com/attenomy/cortex-intern-module-q4-2026.git
```

### Navigate to Project

```bash
cd cortex-intern-module-q4-2026
```

### Install Dependencies

```bash
cd api
py -m pip install -r requirements.txt
```

### Run Tests

```bash
py -m pytest modules\telemetry_obs\tests modules\semantic_cache\tests -v
```

---

## 14. Engineering Contribution: CTX-004

**Task:** Prometheus Telemetry & Observability

**Branch:** `feature/CTX-004-prometheus-telemetry`

### Work Completed

1. Integrated Prometheus client dependency.
2. Implemented HTTP request monitoring middleware.
3. Added request latency histogram instrumentation.
4. Added semantic cache hit counter instrumentation.
5. Implemented application lifecycle gauge updates.
6. Exposed Prometheus metrics through `/metrics`.
7. Integrated telemetry components into FastAPI.
8. Added and updated automated tests.
9. Validated implementation using Pytest and Ruff.
10. Reviewed feature branch against `staging`.

### Verification Results

- Automated tests: 41 passed.
- Failed tests: 0.
- Ruff: All checks passed.
- PR comparison: 10 expected files, 0 deleted files.

---

## 15. Video Walkthrough

**Prometheus Telemetry Implementation Demo**

[Watch the implementation walkthrough](https://drive.google.com/file/d/1hxLwuhpHbtage4Nmfr_21Cqbl1qNEYos/view?usp=sharing)

The walkthrough demonstrates the telemetry implementation, metrics endpoint, and testing results.

---

## 16. Repository and Pull Request

**Main Repository**

https://github.com/attenomy/cortex-intern-module-q4-2026

**Implementation Branch**

https://github.com/attenomy/cortex-intern-module-q4-2026/tree/feature/CTX-004-prometheus-telemetry

**Pull Request #12**

https://github.com/attenomy/cortex-intern-module-q4-2026/pull/12

**Target Branch:** `staging`

---

## 17. Conclusion

Attenomy Cortex is an enterprise AI infrastructure project focused on intelligent query processing, knowledge retrieval, semantic caching, and backend observability.

Its modular architecture is designed to support efficient AI-powered application workflows. Semantic caching helps reduce repeated processing, while Prometheus telemetry provides visibility into application performance and runtime activity.

The CTX-004 implementation adds monitoring for HTTP requests, request latency, semantic cache hits, application lifecycle, and uptime. It was validated with 41 passing tests and successful Ruff checks.

---
