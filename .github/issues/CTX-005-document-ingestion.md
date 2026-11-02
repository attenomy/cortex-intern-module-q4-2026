# [CTX-005] Multi-Source Document Ingestion & Asynchronous Preprocessing Pipeline

> **Ticket ID**: CTX-005  
> **Phase**: Week 3 (Monday - Friday / Days 11 - 15)  
> **Assignee**: Mala Kumari (`@mala9311`)  
> **Module Path**: `api/modules/doc_ingestion/`  
> **Branch**: `feature/CTX-005-doc-ingestion` -> `staging`  
> **Supervisor / Signatory**: Saad Md. (`saad@attenomy.com`), Founder & CPO  

---

## 1. Executive Summary & Problem Context
Autonomous agents in Attenomy Cortex require robust, continuous ingestion of unstructured enterprise data sources (PDF manuals, Markdown technical dossiers, Playwright web crawls, and continuous text streams). The existing baseline ingestion endpoint in `api/modules/doc_ingestion/` provides basic chunking and regex sanitization, but lacks:
* Production-grade asynchronous stream processing with backpressure control.
* Memory-bounded ingestion capable of handling large multi-megabyte payloads without exhausting server RAM.
* Advanced heuristic sanitization against adversarial prompt injections, dangerous script tags, and recursive control characters.
* Deterministic deduplication using cryptographic content hashing (SHA-256) across sliding token windows.

To achieve production release readiness, you must build an enterprise-grade multi-source asynchronous document ingestion pipeline delivering sub-50ms CPU chunking throughput with strict security sanitization and high reliability.

---

## 2. Mathematical Foundations & Constraints
* **Sliding Window Chunking Equation**: For a document string of length $L$, target chunk token window $W$, and overlap stride $S < W$:
  $$\text{Step Size} = W - S, \quad N_{\text{chunks}} = \left\lceil \frac{L - S}{W - S} \right\rceil$$
  Enforce strict invariant: $0 \le S < W \le 4096$.
* **Cryptographic Deduplication**: Each chunk must carry a canonical SHA-256 fingerprint:
  $$H_i = \text{SHA256}(\text{normalized\_text}_i)$$
* **Throughput SLA**: Pipeline must process and chunk at least 100,000 characters per second on multi-core CPU with median latency $< 25\text{ms}$ and p95 $< 50\text{ms}$.
* **Memory Safety Limit**: Ingestion buffer must be bounded to maximum 10MB per request, with streaming memory consumption capped under 50MB.

---

## 3. Strict 5-Day Operational Engineering Schedule (Mon - Fri)

### Day 11 (Monday): Spec-First Data Contracts & Ingestion Schema Architecture
* **Objective**: Define data contracts, validation rules, and error conditions before writing pipeline logic.
* **Deliverables**:
  1. Author `api/modules/doc_ingestion/FEATURE_SPEC.md`.
  2. Define Pydantic schemas in `schemas.py`: `IngestionSourceType` (PDF, Markdown, Plain Text, Web Stream), `IngestionPriority`, `DocumentChunk`, `DocumentIngestRequest`, and `DocumentIngestResponse`.
  3. Formulate the edge-case failure matrix detailing at least 10 critical failure states: empty payloads, invalid chunk overlaps ($S \ge W$), null byte injections, HTML script tag attacks, prompt injection prefixes ("Ignore all previous instructions"), memory limit violations (>10MB), and non-UTF8 binary noise.
  4. Submit specification for CPO architectural review.

### Day 12 (Tuesday): Asynchronous Ingestion Engine & Security Filters
* **Objective**: Implement high-throughput async ingestion engine with security sanitization.
* **Deliverables**:
  1. Implement `api/modules/doc_ingestion/service.py` with non-blocking async execution (`async def ingest_document`).
  2. Implement comprehensive sanitization heuristics: strip executable code snippets, null bytes, non-printable control characters, and flag adversarial prompt injections.
  3. Implement rolling sliding-window chunker with dynamic token estimation and SHA-256 chunk hashing.
  4. Wire up modular FastAPI router endpoints (`POST /api/v1/ingest`, `GET /api/v1/ingest/health`).

### Day 13 (Wednesday): Defensive Verification & Edge-Case Test Suite
* **Objective**: Build comprehensive test coverage enforcing Attenomy's defensive engineering standard (>60% negative test ratio).
* **Deliverables**:
  1. Author at least 12 comprehensive unit and integration tests in `api/modules/doc_ingestion/tests/test_doc_ingestion.py`.
  2. Minimum 60% of tests must target negative and boundary conditions:
     - Empty, whitespace-only, and null-byte payloads (HTTP 400/422).
     - Overlap greater than or equal to chunk size rejection (HTTP 422).
     - Adversarial prompt injection payloads verifying `status == "sanitized"` and redaction flags.
     - Corrupt and non-ASCII binary strings.
     - Maximum payload size boundary tests (>10MB rejection).
  3. Verify `pytest` passes with 100% green status across all test suites.

### Day 14 (Thursday): Hyperparameter Tuning & High-Concurrency Latency Profiling
* **Objective**: Empirical performance profiling and constraint verification under load.
* **Deliverables**:
  1. Conduct systematic tuning experiments across at least 6 runs (chunk sizes [128, 256, 512, 1024], overlap ratios [10%, 20%, 30%], batch ingestion sizes [1, 5, 20]). Document findings in `api/modules/doc_ingestion/reports/tuning_experiments.md`.
  2. Profile execution speed with Python `cProfile` and load testing harness simulating 50 concurrent ingestion requests.
  3. Verify latency SLA: median processing latency under 25ms and p95 under 50ms on CPU.
  4. Use `tracemalloc` across 5,000 document ingestion operations to prove zero memory leaks.

### Day 15 (Friday): Diagnostic Error Analysis, Runbook & Evidence-Driven PR
* **Objective**: Complete formal documentation, runbooks, and defend the implementation.
* **Deliverables**:
  1. Author `api/modules/doc_ingestion/reports/diagnostic_error_analysis.md`: chunk fragmentation metrics, sanitization false positive rates, and performance impact of regex matching.
  2. Author operational runbook `api/modules/doc_ingestion/RUNBOOK.md` detailing supported MIME types, worker thread pool sizing, Prometheus metrics counters, and security alert thresholds.
  3. Open an Evidence-Driven Pull Request (EDPR) targeting `staging` using `.github/PULL_REQUEST_TEMPLATE.md`:
     - Section 1: Architectural Decision Record (ADR).
     - Section 2: Complete terminal output of pytest suite.
     - Section 3: Latency percentile metrics and cProfile graphs proving p95 < 50ms.
     - Section 4: 60-90 second Loom video walkthrough.
     - Section 5: Completed 2-Minute Code Defense checklist.
  4. Schedule live 2-minute code defense session with Lead / CPO Saad Md.

---

## 4. Acceptance Criteria & Quality Gates
* High-throughput asynchronous ingestion pipeline with sub-50ms CPU p95 latency.
* Robust security sanitization: 100% detection of prompt injection and null byte vectors.
* Edge-Case Test Ratio strictly greater than 60%.
* Complete documentation: `FEATURE_SPEC.md`, `RUNBOOK.md`, and `reports/diagnostic_error_analysis.md`.
* 100% pass on live 2-minute code defense explaining async streaming, token estimation, and backpressure handling.
