# [CTX-001] Neural Semantic Intent Router & Sub-50ms CPU Inference Engine

> **Ticket ID**: CTX-001  
> **Phase**: Week 3 (Monday - Friday / Days 11 - 15)  
> **Assignee**: Abhishek Adbhute (`@abhishekadbhute-create`)  
> **Module Path**: `api/modules/intent_router/`  
> **Branch**: `feature/CTX-001-intent-router` -> `staging`  
> **Supervisor / Signatory**: Saad Md. (`saad@attenomy.com`), Founder & CPO  

---

## 1. Executive Summary & Problem Context
The current intent routing module in `api/modules/intent_router/service.py` uses naive keyword sub-string matching (`INTENT_MAPPINGS`) and a simulated sleep interval. In production, this heuristic fails catastrophically when queries:
* Contain multi-intent domain vocabularies (e.g. "Generate invoice billing report after fixing crash bug").
* Use conversational phrasing, synonyms, or non-English terminology.
* Possess adversarial out-of-vocabulary inputs or prompt injections.

To achieve production release readiness, you must replace the keyword lookup with an optimized, lightweight neural transformer classification engine running in ONNX runtime or PyTorch with sub-50ms CPU inference latency at p95.

---

## 2. Mathematical Foundations & Constraints
* **Softmax Probability**: For intent logits $z = (z_1, \dots, z_K)$, compute class probability:
  $$P(\text{class} = k \mid x) = \frac{e^{z_k / T}}{\sum_{j=1}^K e^{z_j / T}}$$
  where temperature $T = 1.0$ by default.
* **Fallback Decision Boundary**: If $\max_k P(k \mid x) < 0.60$, the router must deterministically assign `intent_category = "search"` with `fallback_triggered = True`.
* **Latency Budget**: Median execution time $< 25\text{ms}$ and p95 latency $< 50\text{ms}$ running strictly on multi-core CPU (zero GPU reliance).
* **Memory Bound**: Maximum model memory residency must not exceed 250MB RAM.

---

## 3. Strict 5-Day Operational Engineering Schedule (Mon - Fri)

### Day 11 (Monday): Spec-First Data Contracts & Mathematical Specification
* **Objective**: Define data contracts and verify constraints before writing production implementation.
* **Deliverables**:
  1. Create `api/modules/intent_router/FEATURE_SPEC.md`.
  2. Define Pydantic models for intent classification: `IntentCategory` (Finance, Support, Search, Orchestration), `TopKCandidate`, `IntentRoutingRequest`, and `RoutingDecision`.
  3. Formalize the edge-case failure matrix documenting 10+ failure modes: zero-length strings, whitespace, 10,000-character payload limits, emoji-only strings, multilingual inputs, and SQL injection strings.
  4. Submit specification to Lead / CPO for approval before writing model logic.

### Day 12 (Tuesday): Neural Model Architecture & ONNX Optimization
* **Objective**: Build the neural inference pipeline and eliminate cold-start latency.
* **Deliverables**:
  1. Select and package a lightweight embedding/classification model (e.g. `all-MiniLM-L6-v2` or `distilbert-base-uncased-finetuned`) exported to ONNX format for zero-overhead CPU execution.
  2. Implement `api/modules/intent_router/service.py` using `onnxruntime.InferenceSession` with `GraphOptimizationLevel.ORT_ENABLE_ALL` and intra-op thread pooling.
  3. Wire up lifespan warm-up logic during FastAPI application startup: execute a dummy inference on boot so initial production requests experience zero cold-start delay.
  4. Implement Top-3 candidate ranking with calibrated confidence scores.

### Day 13 (Wednesday): Defensive Verification & Edge-Case Test Suite
* **Objective**: Build rigorous test coverage enforcing Attenomy's defensive engineering standard (>60% negative test ratio).
* **Deliverables**:
  1. Author at least 12 comprehensive unit and integration tests in `api/modules/intent_router/tests/test_intent_router.py`.
  2. Minimum 60% of tests must target negative and boundary conditions:
     - Missing and empty query payloads (HTTP 400/422).
     - Adversarial strings with repeated tokens exceeding token buffer limits.
     - Ambiguous dual-intent queries verifying calibrated confidence decay.
     - Out-of-vocabulary and random ASCII character noise triggering fallback mode.
     - Rapid consecutive requests verifying stateless thread safety.
  3. Verify `pytest` passes with 100% green status across all test suites.

### Day 14 (Thursday): Hyperparameter Tuning & High-Concurrency Latency Profiling
* **Objective**: Empirical performance profiling and constraint verification under load.
* **Deliverables**:
  1. Perform systematic hyperparameter exploration across at least 6 experiment runs (e.g. batch sizes [1, 4, 16], sequence lengths [64, 128, 256], quantization INT8 vs FP32). Document results in `api/modules/intent_router/reports/tuning_experiments.md`.
  2. Conduct high-concurrency profiling using Python `cProfile` and load testing (Locust or `asyncio` concurrent worker harness) simulating 50 concurrent requests.
  3. Generate latency percentile distribution proof: p50, p90, p95, and p99. Ensure p95 is strictly under 50ms on CPU.
  4. Run memory profiling with `tracemalloc` across 5,000 continuous requests to prove zero memory leaks.

### Day 15 (Friday): Diagnostic Error Analysis, Runbook & Evidence-Driven PR
* **Objective**: Complete formal documentation, runbooks, and defend the implementation.
* **Deliverables**:
  1. Author `api/modules/intent_router/reports/diagnostic_error_analysis.md`: confusion matrix analysis, misclassification edge cases, and rationale for rejected architectures.
  2. Author operational runbook `api/modules/intent_router/RUNBOOK.md` detailing startup sequence, environment flags, Prometheus metrics counters, and rollback procedures.
  3. Open an Evidence-Driven Pull Request (EDPR) targeting `staging` using `.github/PULL_REQUEST_TEMPLATE.md`:
     - Section 1: Architectural Decision Record (ADR).
     - Section 2: Complete terminal output of pytest suite.
     - Section 3: Latency percentile metrics and cProfile graphs proving p95 < 50ms.
     - Section 4: 60-90 second Loom video walkthrough.
     - Section 5: Completed 2-Minute Code Defense checklist.
  4. Schedule live 2-minute code defense session with Lead / CPO Saad Md.

---

## 4. Acceptance Criteria & Quality Gates
* Real neural inference replaces keyword heuristic.
* Fast response time: p95 latency strictly under 50ms on CPU.
* Edge-Case Test Ratio strictly greater than 60%.
* Complete documentation: `FEATURE_SPEC.md`, `RUNBOOK.md`, and `reports/diagnostic_error_analysis.md`.
* 100% pass on live 2-minute code defense explaining tensor operations and thread safety.
