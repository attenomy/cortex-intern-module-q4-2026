# Attenomy Cortex Production Issue Backlog (Weeks 3 & 4)

> **Organisation**: Attenomy, Udyam-registered MSME (UDYAM-TS-02-0279596)  
> **Repository**: apps/attenomy-cortex  
> **Phase**: Weeks 3 & 4 (Cohort Q4 2026)  
> **Lead / Signatory**: Saad Md. (`saad@attenomy.com`), Founder & CPO  

This document contains the official production feature backlog for Machine Learning and Systems Engineering contributors transitioning into the **Product Contribution Phase (Weeks 3 and 4)** on **Attenomy Cortex**.

To combat the shallow "10-minute intern" AI prompting trap, each issue is structured across a rigorous **5-day operational lifecycle (Monday - Friday / Days 11 - 15)**. Interns must design contracts before prompting, enforce defensive test ratios (>60% negative tests), conduct hyperparameter tuning, profile CPU latencies under load, and defend their code in a live 2-minute walkthrough.

All contributors branch off `staging` using the branch naming convention `feature/<ticket-id>-<slug>` (e.g. `feature/CTX-001-intent-router`) and submit an Evidence-Driven Pull Request (EDPR) following `CONTRIBUTING.md`.

---

## 1. Ticket Overview Matrix

| Ticket ID | Phase | Category | Assigned Engineer | Target Component | Core Metric / Constraint |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`[CTX-001]`** | Week 3 | NLP / Routing | Abhishek Adbhute (`@abhishekadbhute-create`) | `api/modules/intent_router/` | p95 inference latency < 50ms on CPU; accuracy > 92% |
| **`[CTX-002]`** | Week 3 | Vision / DocAI | Abhinav Singh (`@Abhinav55849`) | `api/modules/doc_extractor/` | Layout classification macro F1 > 0.90; schema validation |
| **`[CTX-003]`** | Week 3 | Systems / Cache | Yakshith Anandapu (`@YAKSHITH684`) | `api/modules/semantic_cache/` | Redis cache hit latency < 5ms; > 50% duplicate avoidance |
| **`[CTX-005]`** | Week 3 | ETL / Ingestion | Mala Kumari (`@mala9311`) | `api/modules/doc_ingestion/` | Asynchronous chunking < 50ms p95; prompt injection sanitization |
| **`[CTX-004]`** | Week 4 | DevOps / Infra | Cohort Collaboration | `Dockerfile`, CI & Prometheus | Multi-stage non-root build; 100% CI pass rate |

---

## 2. Detailed Issue Specifications

### [CTX-001] Neural Semantic Intent Router & Sub-50ms CPU Inference Engine
* **Assigned Engineer**: Abhishek Adbhute (`@abhishekadbhute-create`)
* **Component**: `api/modules/intent_router/` (replacing keyword dictionary heuristic).
* **Business Objective**: Route incoming natural language queries to specialized agent sub-graphs (Finance, Support, Search, Orchestration) with high precision and sub-50ms CPU execution.
* **5-Day Mon-Fri Roadmap**:
  - **Day 11 (Mon)**: Author `FEATURE_SPEC.md`, Pydantic schemas, and 10+ failure case matrix.
  - **Day 12 (Tue)**: Model export to ONNX runtime, lifespan warm-up on startup, Top-3 ranking with confidence calibration.
  - **Day 13 (Wed)**: Build 12+ unit/integration tests with >60% negative test ratio (adversarial inputs, empty strings, fallback triggers).
  - **Day 14 (Thu)**: Systematic tuning across 6+ runs (quantization INT8 vs FP32, batch sizes), Locust latency profiling (p95 < 50ms).
  - **Day 15 (Fri)**: Diagnostic error analysis memo, `RUNBOOK.md`, and Evidence-Driven PR (EDPR) with Loom demo.

---

### [CTX-002] Cognitive Document Entity Extractor & Layout Classifier
* **Assigned Engineer**: Abhinav Singh (`@Abhinav55849`)
* **Component**: `api/modules/doc_extractor/` (replacing mock invoice dictionary).
* **Business Objective**: Autonomous agent ingestion and entity extraction from enterprise invoices, receipts, and purchase orders.
* **5-Day Mon-Fri Roadmap**:
  - **Day 11 (Mon)**: Author `FEATURE_SPEC.md`, Pydantic schemas for extracted entities and bounding boxes, and error taxonomy.
  - **Day 12 (Tue)**: MobileNetV3 / OpenCV spatial layout clustering pipeline, pre-warmed weights on boot, field validation.
  - **Day 13 (Wed)**: Build 12+ unit/integration tests with >60% negative test ratio (corrupt base64, missing keys, boundary formats).
  - **Day 14 (Thu)**: Systematic tuning across 6+ runs (resolution, confidence thresholds), cProfile latency profiling (< 300ms p95).
  - **Day 15 (Fri)**: Diagnostic error analysis memo (macro F1 > 0.90), `RUNBOOK.md`, and Evidence-Driven PR (EDPR) with Loom demo.

---

### [CTX-003] Redis Semantic Vector Caching & Query Deduplication Engine
* **Assigned Engineer**: Yakshith Anandapu (`@YAKSHITH684`)
* **Component**: `api/modules/semantic_cache/`
* **Business Objective**: Serve semantically identical queries from a Redis vector cache within 5ms to avoid redundant downstream inference.
* **5-Day Mon-Fri Roadmap**:
  - **Day 11 (Mon)**: Author `FEATURE_SPEC.md`, cache key schemas, vector quantization models, and eviction policies.
  - **Day 12 (Tue)**: Async Redis client with connection pooling, cosine similarity search, background writes, and fail-open breaker.
  - **Day 13 (Wed)**: Build 12+ unit/integration tests with >60% negative test ratio (Redis outage simulation, dimension mismatch, empty queries).
  - **Day 14 (Thu)**: Systematic tuning across 6+ runs (similarity threshold 0.95, pool size), load testing (p95 < 5ms).
  - **Day 15 (Fri)**: Diagnostic error analysis memo, `RUNBOOK.md`, and Evidence-Driven PR (EDPR) with Loom demo.

---

### [CTX-005] Multi-Source Document Ingestion & Asynchronous Preprocessing Pipeline
* **Assigned Engineer**: Mala Kumari (`@mala9311`)
* **Component**: `api/modules/doc_ingestion/`
* **Business Objective**: High-throughput multi-source document ingestion, prompt injection sanitization, and sliding-window chunking.
* **5-Day Mon-Fri Roadmap**:
  - **Day 11 (Mon)**: Author `FEATURE_SPEC.md`, Pydantic schemas, sliding-window mathematical specification, and security threat model.
  - **Day 12 (Tue)**: Async ingestion engine, prompt injection filtering, null byte stripping, and SHA-256 chunk deduplication.
  - **Day 13 (Wed)**: Build 12+ unit/integration tests with >60% negative test ratio (injection payloads, overlap errors, oversized files).
  - **Day 14 (Thu)**: Systematic tuning across 6+ runs (chunk sizes, overlap ratios), concurrency latency profiling (p95 < 50ms).
  - **Day 15 (Fri)**: Diagnostic error analysis memo, `RUNBOOK.md`, and Evidence-Driven PR (EDPR) with Loom demo.

---

### [CTX-004] Hardened Containerization, Prometheus Metrics & Automated CI
* **Assigned Engineer**: Cohort Collaboration (Week 4 Capstone)
* **Component**: `api/Dockerfile`, `api/modules/telemetry_obs/`, `.github/workflows/cortex-ci.yml`
* **Business Objective**: Enterprise deployment isolation, automated CI regression verification, and Prometheus observability.
* **5-Day Mon-Fri Roadmap**:
  - **Day 16 (Mon)**: Threat modeling, container architecture specification, and Prometheus metric taxonomy.
  - **Day 17 (Tue)**: Multi-stage slim Dockerfile running under non-root `USER attenomy` (UID 10001), healthchecks, docker-compose.
  - **Day 18 (Wed)**: Prometheus metrics middleware on `GET /metrics`, request latency histograms, unit tests.
  - **Day 19 (Thu)**: GitHub Actions CI workflow running Ruff linting, security scanning, and full Pytest regression suite.
  - **Day 20 (Fri)**: Operational runbook, container CVE scan, and cohort live code defense.
