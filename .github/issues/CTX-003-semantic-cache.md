# [CTX-003] Redis Semantic Vector Caching & Query Deduplication Engine

> **Ticket ID**: CTX-003  
> **Phase**: Week 3 (Monday - Friday / Days 11 - 15)  
> **Assignee**: Yakshith Anandapu (`@YAKSHITH684`)  
> **Module Path**: `api/modules/semantic_cache/`  
> **Branch**: `feature/CTX-003-semantic-cache` -> `staging`  
> **Supervisor / Signatory**: Saad Md. (`saad@attenomy.com`), Founder & CPO  

---

## 1. Executive Summary & Problem Context
Every incoming query to Attenomy Cortex currently invokes downstream neural classification and LLM inference, even when identical or semantically equivalent queries were processed milliseconds earlier. In high-throughput production environments, this results in:
* Unnecessary CPU and memory exhaustion under duplicate traffic.
* High average latency for frequently repeated enterprise workflows.
* Catastrophic service degradation during Redis connection blips if caching is tightly coupled.

To achieve production release readiness, you must build a high-performance Redis vector caching and query deduplication engine delivering cache hits in under 5.0ms with automatic fail-open resilience.

---

## 2. Mathematical Foundations & Constraints
* **Cosine Similarity Metric**: For incoming query vector $u \in \mathbb{R}^d$ and stored cache vectors $v_i \in \mathbb{R}^d$:
  $$\text{sim}(u, v_i) = \frac{u \cdot v_i}{\|u\|_2 \, \|v_i\|_2}$$
* **Threshold Decision Gate**:
  - If $\max_i \text{sim}(u, v_i) \ge 0.95$: Return cached response immediately with `cached: true` and latency $< 5.0\text{ms}$.
  - If $\max_i \text{sim}(u, v_i) < 0.95$: Execute live inference, store $(u, \text{result})$ asynchronously with 24-hour TTL, and return `cached: false`.
* **Fail-Open Resilience**: If Redis becomes unreachable (timeout, network partition, connection refused), the system must log an alert, bypass cache, and execute live routing without throwing HTTP 500 errors.

---

## 3. Strict 5-Day Operational Engineering Schedule (Mon - Fri)

### Day 11 (Monday): Spec-First Data Contracts & Vector Schema Design
* **Objective**: Define cache schemas, vector key spaces, and invalidation rules before writing service code.
* **Deliverables**:
  1. Author `api/modules/semantic_cache/FEATURE_SPEC.md`.
  2. Define Pydantic schemas in `schemas.py`: `CacheLookupRequest`, `CacheLookupResponse`, `CacheInvalidationRequest`, and `CacheStatsResponse`.
  3. Formulate the edge-case failure matrix detailing at least 10 critical failure states: Redis connection timeouts, malformed vector dimensions, empty query keys, concurrent write collisions, TTL expirations, and memory eviction policies (`volatile-lru`).
  4. Submit specification for CPO architectural review.

### Day 12 (Tuesday): Redis Vector Search & Asynchronous Caching Engine
* **Objective**: Implement high-throughput caching service with non-blocking I/O.
* **Deliverables**:
  1. Implement `api/modules/semantic_cache/service.py` using `redis-py` async client with connection pooling (`BlockingConnectionPool(max_connections=50)`).
  2. Implement Redis vector search or optimized approximate nearest neighbor (ANN) index over normalized query embeddings.
  3. Implement asynchronous background cache write (`BackgroundTasks` or `asyncio.create_task`) so caching never blocks downstream client response times.
  4. Implement fail-open circuit breaker logic: wrap Redis I/O in a resilient fallback context manager catching `ConnectionError` and `TimeoutError`.

### Day 13 (Wednesday): Defensive Verification & Edge-Case Test Suite
* **Objective**: Build comprehensive test coverage enforcing Attenomy's defensive engineering standard (>60% negative test ratio).
* **Deliverables**:
  1. Author at least 12 comprehensive unit and integration tests in `api/modules/semantic_cache/tests/test_semantic_cache.py`.
  2. Minimum 60% of tests must target negative and boundary conditions:
     - Redis connection drop / paused container simulation proving zero 500 errors.
     - Empty, whitespace, or oversized query inputs (HTTP 400/422).
     - Vector dimension mismatches.
     - Query similarity at boundary thresholds (e.g. 0.949 vs 0.951).
     - Simultaneous concurrent writes to identical query keys (race condition resistance).
  3. Verify `pytest` passes with 100% green status across all test suites.

### Day 14 (Thursday): Hyperparameter Tuning & High-Concurrency Latency Profiling
* **Objective**: Empirical performance profiling and constraint verification under load.
* **Deliverables**:
  1. Perform systematic hyperparameter exploration across at least 6 experiment runs (similarity thresholds [0.90, 0.95, 0.98], Redis connection pool sizes [10, 25, 50], vector dimensionality [128, 384, 768]). Document findings in `api/modules/semantic_cache/reports/tuning_experiments.md`.
  2. Profile execution speed with `cProfile` and load testing harness simulating 100 concurrent cache lookups.
  3. Prove cache hit latency is strictly under 5.0ms at p95 and duplicate traffic avoidance exceeds 50%.
  4. Run memory profiling across 10,000 cached records to verify memory footprint stays within allocated limits.

### Day 15 (Friday): Diagnostic Error Analysis, Runbook & Evidence-Driven PR
* **Objective**: Complete formal documentation, runbooks, and defend the implementation.
* **Deliverables**:
  1. Author `api/modules/semantic_cache/reports/diagnostic_error_analysis.md`: false positive cache hit rate, impact of semantic drift, and benchmark comparison between exact match vs vector search.
  2. Author operational runbook `api/modules/semantic_cache/RUNBOOK.md` detailing Redis configuration parameters, memory eviction alerts, and cache flush operational procedures.
  3. Open an Evidence-Driven Pull Request (EDPR) targeting `staging` using `.github/PULL_REQUEST_TEMPLATE.md`:
     - Section 1: Architectural Decision Record (ADR).
     - Section 2: Complete terminal output of pytest suite.
     - Section 3: Latency percentile metrics and cProfile graphs proving cache hit < 5ms.
     - Section 4: 60-90 second Loom video walkthrough.
     - Section 5: Completed 2-Minute Code Defense checklist.
  4. Schedule live 2-minute code defense session with Lead / CPO Saad Md.

---

## 4. Acceptance Criteria & Quality Gates
* Cache hit latency strictly under 5.0ms at p95.
* Fail-open resilience verified: service functions seamlessly during Redis downtime.
* Edge-Case Test Ratio strictly greater than 60%.
* Complete documentation: `FEATURE_SPEC.md`, `RUNBOOK.md`, and `reports/diagnostic_error_analysis.md`.
* 100% pass on live 2-minute code defense explaining async connection pooling and vector index mechanics.
