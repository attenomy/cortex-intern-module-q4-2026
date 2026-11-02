# Attenomy Cortex Intern Module Assignments & PR Workflow (Weeks 3 & 4)

> **Organisation**: Attenomy, Udyam-registered MSME (UDYAM-TS-02-0279596)  
> **Repository**: apps/attenomy-cortex  
> **Engineering Protocol**: Attenomy SOP-04 & Evidence-Driven PR Protocol  
> **Lead / Signatory**: Saad Md. (`saad@attenomy.com`), Founder & CPO  

---

## 1. Executive Summary & Modular Ownership Model
To eliminate merge conflicts, avoid cross-team blockers, and enforce true engineering ownership, **Attenomy Cortex** is partitioned into encapsulated domain modules. Each intern owns one complete operational slice: schema definitions, service logic, test suites, latency profiling, and runbooks.

To combat the shallow "10-minute intern" AI prompting trap, each issue is scoped across a rigorous **5-day operational lifecycle (Monday - Friday / Days 11 - 15)**. Interns must design contracts before prompting, enforce defensive test ratios (>60% negative tests), conduct hyperparameter tuning, profile CPU latencies under load, and defend their code in a live 2-minute walkthrough.

---

## 2. Cohort 2026 Q4 Intern Assignments Matrix

| Assigned Intern | GitHub Handle | Assigned Module Path | Ticket ID | Target Branch | Phase | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Abhishek Adbhute** | `@abhishekadbhute-create` | `api/modules/intent_router/` | `[CTX-001]` | `feature/CTX-001-intent-router` | Week 3 | **ASSIGNED** |
| **Abhinav Singh** | `@Abhinav55849` | `api/modules/doc_extractor/` | `[CTX-002]` | `feature/CTX-002-doc-extractor` | Week 3 | **ASSIGNED** |
| **Yakshith Anandapu** | `@YAKSHITH684` | `api/modules/semantic_cache/` | `[CTX-003]` | `feature/CTX-003-semantic-cache` | Week 3 | **ASSIGNED** |
| **Mala Kumari** | `@mala9311` | `api/modules/doc_ingestion/` | `[CTX-005]` | `feature/CTX-005-doc-ingestion` | Week 3 | **ASSIGNED** |
| **Cohort Collaboration** | All Selects | `api/modules/telemetry_obs/` | `[CTX-004]` | `feature/CTX-004-observability-ci` | Week 4 Capstone | **PLANNED** |

---

## 3. Mandatory 5-Day Operational Engineering Lifecycle (Mon - Fri)

Every assigned intern must execute the following structured 5-day engineering roadmap:

```
[Monday: Spec-First Design] ──> [Tuesday: Core Architecture & ONNX] ──> [Wednesday: Defensive Edge Tests]
                                                                                       │
                                                                                       ▼
[Merged to Staging] <── [Live 2-Min Defense] <── [Friday: Diagnostic Memo & EDPR] <── [Thursday: Tuning & Latency Profile]
```

### Day 11 (Monday): Spec-First Data Contracts & Schema Architecture
* Author `FEATURE_SPEC.md` inside your module directory.
* Define Pydantic models, validation rules, and error states.
* Formalize the edge-case failure matrix (minimum 10 distinct negative conditions).
* Review specification with Lead / CPO before writing implementation.

### Day 12 (Tuesday): Core Model Architecture & Optimized Implementation
* Implement core service logic in `service.py`.
* For ML modules: model quantization, ONNX export, and lifespan warm-up on boot.
* For Systems/ETL modules: non-blocking asynchronous processing, backpressure, and chunking.
* Wire endpoints into the modular FastAPI router.

### Day 13 (Wednesday): Defensive Verification & Edge-Case Test Suite
* Build comprehensive test suite in `tests/`. Minimum 12-15 unit and integration tests.
* **Defensive Engineering Rule**: Minimum 60% of tests must target negative and boundary conditions (empty strings, corrupt payloads, dimension mismatches, network drops).
* Verify 100% green test pass rate across the full API regression suite.

### Day 14 (Thursday): Hyperparameter Tuning & High-Concurrency Latency Profiling
* Perform systematic tuning experiments across at least 6 runs (batch sizes, quantization, thresholds). Document in `reports/tuning_experiments.md`.
* Run high-concurrency profiling with `cProfile` and load tests (Locust or async worker harness).
* Verify SLA constraints: median latency < 25ms, p95 < 50ms strictly on CPU.
* Memory profiling with `tracemalloc` across 5,000 requests to prove zero memory leaks.

### Day 15 (Friday): Diagnostic Error Analysis, Operational Runbook & EDPR
* Author `reports/diagnostic_error_analysis.md` and operational runbook `RUNBOOK.md`.
* Open Evidence-Driven Pull Request (EDPR) against `staging` with all 5 mandatory sections:
  1. Architectural Decision Record (ADR)
  2. Raw terminal test execution logs
  3. Latency percentile proof (cProfile / Locust output)
  4. 60-90s Loom video walkthrough
  5. Contributor Code Defense prep checklist
* Complete live 2-minute code defense walkthrough with Lead / CPO Saad Md.

---

## 4. Production Engineering Productivity Scorecard

| Metric Name | Mathematical Definition | Target Benchmark | Operational Focus |
| :--- | :--- | :--- | :--- |
| **Defect Escape Rate** | `(Bugs found in Staging or Prod / Total Bugs Logged) * 100` | Under 5% | True verification rigor before merging |
| **Edge-Case Test Ratio** | `Number of Negative & Edge Tests / Total Tests Written` | Greater than 60% | Defensive engineering and failure testing |
| **Code Defense Pass Rate** | `Successful Live Code Explanations / Total Defenses Conducted` | 100% | Full comprehension of committed logic |
| **CPU Latency SLA** | p95 latency under concurrent load on CPU | Under 50ms | Real-time performance without GPU cost |
