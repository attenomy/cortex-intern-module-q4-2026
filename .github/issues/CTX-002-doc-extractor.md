# [CTX-002] Cognitive Document Entity Extractor & Layout Classifier

> **Ticket ID**: CTX-002  
> **Phase**: Week 3 (Monday - Friday / Days 11 - 15)  
> **Assignee**: Abhinav Singh (`@Abhinav55849`)  
> **Module Path**: `api/modules/doc_extractor/`  
> **Branch**: `feature/CTX-002-doc-extractor` -> `staging`  
> **Supervisor / Signatory**: Saad Md. (`saad@attenomy.com`), Founder & CPO  

---

## 1. Executive Summary & Problem Context
The `/api/v1/extract` endpoint in `api/modules/doc_extractor/service.py` currently returns a mocked JSON dictionary without performing real document vision parsing, optical bounding box computation, or entity field validation. In production, this fails when encountering:
* Invoices with missing required fields or non-standard layouts.
* Truncated, malformed, or oversized base64 image strings.
* Unrecognized currency symbols, negative totals, or conflicting tax calculations.

To achieve production release readiness, you must replace the mock payload with an end-to-end cognitive document extraction and layout classification pipeline with high classification accuracy (macro F1 > 0.90) and resilient schema validation.

---

## 2. Mathematical Foundations & Evaluation Metrics
* **Classification Macro F1**: Evaluate entity extraction performance across key document classes (Invoices, Receipts, Purchase Orders, Tax Forms):
  $$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
  Must achieve Macro $F_1 \ge 0.90$ across evaluation test sets.
* **Bounding Box Intersection over Union (IoU)**: For detected entity coordinates $B_{\text{pred}}$ and ground truth $B_{\text{gt}}$:
  $$\text{IoU} = \frac{\text{Area}(B_{\text{pred}} \cap B_{\text{gt}})}{\text{Area}(B_{\text{pred}} \cup B_{\text{gt}})} \ge 0.75$$
* **Schema Validation Constraint**: All extracted financial entities must pass strict Pydantic parsing with bounded numeric floats (`net_amount > 0.0`, ISO-4217 currency code validation).

---

## 3. Strict 5-Day Operational Engineering Schedule (Mon - Fri)

### Day 11 (Monday): Spec-First Data Contracts & Schema Architecture
* **Objective**: Define document contracts, boundary constraints, and error taxonomies.
* **Deliverables**:
  1. Author `api/modules/doc_extractor/FEATURE_SPEC.md`.
  2. Define rigorous Pydantic schemas in `schemas.py`: `DocumentType` (Invoice, Receipt, Contract, Purchase Order), `ExtractedEntity`, `BoundingBox`, `ExtractionRequest`, and `ExtractionResponse`.
  3. Formalize the edge-case failure matrix detailing at least 10 critical failure states: corrupt base64 headers, missing vendor names, zero or negative totals, non-UTF8 OCR outputs, rotated documents, and multi-page buffer overruns.
  4. Submit specification for CPO architectural review.

### Day 12 (Tuesday): Multimodal Pipeline & Layout Classification Engine
* **Objective**: Implement real document parsing and OCR layout classification.
* **Deliverables**:
  1. Build feature extractor pipeline in `api/modules/doc_extractor/service.py` leveraging lightweight PyTorch vision models (e.g. `MobileNetV3` or OpenCV spatial layout analyzers).
  2. Implement spatial layout clustering to detect table columns, key-value invoice blocks, and total summary sections.
  3. Wire up lifespan warm-up logic on startup: load OCR/vision models into memory during boot to avoid cold-start overhead.
  4. Ensure graceful degradation: if an optional field is missing, return `null` with low confidence rather than aborting the pipeline.

### Day 13 (Wednesday): Defensive Verification & Edge-Case Test Suite
* **Objective**: Build comprehensive test coverage enforcing Attenomy's defensive engineering standard (>60% negative test ratio).
* **Deliverables**:
  1. Author at least 12 comprehensive unit and integration tests in `api/modules/doc_extractor/tests/test_doc_extractor.py`.
  2. Minimum 60% of tests must target negative and boundary conditions:
     - Invalid base64 strings and non-image payloads (HTTP 422).
     - Empty document IDs and whitespace payloads (HTTP 400).
     - Missing mandatory invoice keys (`net_amount`, `vendor_name`).
     - Documents with corrupt EXIF metadata and extreme aspect ratios.
     - Synthetic stress payloads simulating memory spikes.
  3. Verify `pytest` passes with 100% green status across all test suites.

### Day 14 (Thursday): Hyperparameter Tuning & High-Concurrency Latency Profiling
* **Objective**: Empirical performance profiling and constraint verification under load.
* **Deliverables**:
  1. Conduct systematic tuning experiments across at least 6 runs (image resolution scaling [512x512, 1024x1024], confidence threshold filters [0.50, 0.70, 0.85], OCR preprocessing denoise kernels). Document findings in `api/modules/doc_extractor/reports/tuning_experiments.md`.
  2. Profile execution speed with `cProfile` and load testing harness simulating 20 concurrent document extractions.
  3. Verify execution latency: median response time under 150ms and p95 under 300ms on CPU.
  4. Use `tracemalloc` to prove memory allocation returns to baseline after garbage collection (zero leaked image buffers).

### Day 15 (Friday): Diagnostic Error Analysis, Runbook & Evidence-Driven PR
* **Objective**: Complete formal documentation, runbooks, and defend the implementation.
* **Deliverables**:
  1. Author `api/modules/doc_extractor/reports/diagnostic_error_analysis.md`: confusion matrix for document types, error rate on degraded scans, and mitigation strategies for blurry documents.
  2. Author operational runbook `api/modules/doc_extractor/RUNBOOK.md` covering deployment instructions, maximum file size configurations, Prometheus metrics gauges, and alert thresholds.
  3. Open an Evidence-Driven Pull Request (EDPR) targeting `staging` using `.github/PULL_REQUEST_TEMPLATE.md`:
     - Section 1: Architectural Decision Record (ADR).
     - Section 2: Complete terminal output of pytest suite.
     - Section 3: Latency percentile metrics and cProfile graphs.
     - Section 4: 60-90 second Loom video walkthrough.
     - Section 5: Completed 2-Minute Code Defense checklist.
  4. Schedule live 2-minute code defense session with Lead / CPO Saad Md.

---

## 4. Acceptance Criteria & Quality Gates
* Real layout classification and entity extraction replaces mock dictionary.
* Macro F1 score strictly exceeds 0.90 on evaluation invoices.
* Edge-Case Test Ratio strictly greater than 60%.
* Complete documentation: `FEATURE_SPEC.md`, `RUNBOOK.md`, and `reports/diagnostic_error_analysis.md`.
* 100% pass on live 2-minute code defense explaining OCR pipeline mechanics and memory limits.
