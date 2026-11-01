# Attenomy Cortex Production Issue Backlog (Weeks 3 & 4)

This document contains the official production feature backlog for Machine Learning and Systems Engineering contributors transitioning into the **Product Contribution Phase (Weeks 3 and 4)** on **Attenomy Cortex**.

All contributors branch off `staging` using the branch naming convention `feature/<ticket-id>-<slug>` (e.g. `feature/CTX-001-neural-intent-router`) and submit an Evidence-Driven Pull Request (EDPR) following `CONTRIBUTING.md`.

---

## Ticket Overview Matrix

| Ticket ID | Phase | Category | Target Component | Core Metric / Constraint |
| :--- | :--- | :--- | :--- | :--- |
| **`[CTX-001]`** | Week 3 | NLP / Routing | `api/services/router.py` | p95 inference latency < 50ms on CPU; accuracy > 92% |
| **`[CTX-002]`** | Week 3 | Vision / DocAI | `api/main.py` (`/api/v1/extract`) | Layout classification macro F1 > 0.90; schema validation |
| **`[CTX-003]`** | Week 4 | Systems / Cache | `api/services/cache.py` | Redis cache hit latency < 5ms; > 50% duplicate avoidance |
| **`[CTX-004]`** | Week 4 | DevOps / Infra | `Dockerfile`, CI & Prometheus | Multi-stage non-root build; 100% CI pass rate |

---

## Detailed Issue Specifications

### [CTX-001] Neural Semantic Intent Router & Sub-50ms Inference Engine
* **Component**: `api/services/router.py` (replacing keyword dictionary heuristic).
* **Business Objective**: Attenomy Cortex must route incoming natural language queries to specialized agent sub-graphs (Finance, Support, Search, Orchestration) with high precision and sub-50ms CPU execution.
* **Current State**: `api/services/router.py` currently relies on a static keyword dictionary (`INTENT_MAPPINGS`) and a simulated sleep timer.
* **Scope of Work**:
  1. Fine-tune a lightweight transformer model (`DistilBERT` or `all-MiniLM-L6-v2`) or export an optimized ONNX runtime model.
  2. Implement warm-up logic during FastAPI lifespan startup to eliminate cold-start latency.
  3. Support confidence scores, Top-3 alternative candidate routing, and a deterministic fallback category when confidence falls below 0.60.
  4. Benchmark CPU latency under concurrent loads proving median < 25ms and p95 < 50ms.
* **Acceptance Criteria**:
  - Replaces keyword heuristic with real neural inference.
  - Returns structured `RoutingDecision` schema matching `api/schemas.py`.
  - p95 inference latency under 50ms benchmarked via Locust or cProfile.
  - Minimum 6 unit and edge-case tests in `tests/test_router.py`.

---

### [CTX-002] Cognitive Document Entity Extractor & Layout Classifier
* **Component**: `api/main.py` (`/api/v1/extract`) and new service module `api/services/extractor.py`.
* **Business Objective**: Enable autonomous agent ingestion of enterprise invoices, receipts, contracts, and purchase orders.
* **Current State**: `/api/v1/extract` endpoint returns a hardcoded mock invoice dictionary.
* **Scope of Work**:
  1. Implement a fine-tuned layout classification pipeline (using PyTorch `MobileNetV3` or OpenCV document feature extractors).
  2. Implement schema validation confirming extracted fields contain required invoice/receipt keys (`vendor_name`, `invoice_number`, `net_amount`, `currency`).
  3. Return explicit HTTP 422 errors for unparseable or corrupted payload content.
  4. Ensure pre-warmed weights load into memory on service startup (`@app.on_event('startup')`).
* **Acceptance Criteria**:
  - Endpoint executes real extraction pipeline and populates `ExtractionResponse`.
  - Validates bounding box coordinates or text entity dictionaries.
  - Handles corrupted base64 or unreadable image payloads gracefully without 500 crashes.
  - Minimum 5 unit and validation tests in `tests/test_extract.py`.

---

### [CTX-003] Redis Semantic Vector Caching & Query Deduplication Engine
* **Component**: `api/services/cache.py` and integration in `api/main.py`.
* **Business Objective**: Prevent redundant LLM and neural routing calls by serving semantically identical queries from a Redis vector cache within 5ms.
* **Scope of Work**:
  1. Build a Redis-backed semantic caching service using cosine similarity over query embeddings.
  2. If cosine similarity between incoming query and cached vector exceeds 0.95, return cached `RoutingDecision` with `cached=True` in < 5ms.
  3. If similarity is below threshold, execute neural router and asynchronously cache the new query embedding with a 24-hour TTL.
  4. Graceful degradation: if Redis connection drops, fail open by falling back directly to neural router without throwing errors.
* **Acceptance Criteria**:
  - Redis cache hit returns result in under 5ms.
  - Sets `cached: true` in the JSON response when served from cache.
  - Offline fallback test proves system routes normally if Redis container is paused.
  - Unit tests verifying cache hit, cache miss, and connection drop scenarios.

---

### [CTX-004] Hardened Containerization, Prometheus Metrics & Automated CI
* **Component**: `api/Dockerfile`, `api/main.py`, and `.github/workflows/cortex-ci.yml`.
* **Business Objective**: Provide enterprise-grade production infrastructure and deployment repeatability.
* **Scope of Work**:
  1. Re-engineer `api/Dockerfile` into a multi-stage slim container running under a dedicated non-root user (`USER attenomy`, UID 10001).
  2. Expose Prometheus metrics endpoint (`GET /metrics`) tracking request count, error status codes, and inference latency histograms.
  3. Build GitHub Actions CI pipeline running Ruff linting, security scans, and Pytest test suite on every pull request targeting `main` or `staging`.
  4. Validate `docker-compose up` launches `cortex-api` and `cortex-redis` with healthy connectivity.
* **Acceptance Criteria**:
  - Docker container builds cleanly with zero root permissions and no unneeded build tools.
  - `GET /metrics` outputs standard Prometheus format metrics.
  - GitHub Actions workflow executes and passes with zero warnings.

