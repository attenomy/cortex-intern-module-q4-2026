# Module E: Multi-Source Document Ingestion & Asynchronous Preprocessing Pipeline

> **Module**: `api/modules/doc_ingestion/`  
> **Ticket**: `[CTX-005]`  
> **Assigned Engineer**: Mala Kumari (`@mala9311`)  
> **Target Branch**: `feature/CTX-005-doc-ingestion`  
> **Direct Supervisor**: Saad Md. (`saad@attenomy.com`), Founder & CPO  

---

## 1. Module Overview & Production Objective
Attenomy Cortex must ingest multi-format enterprise documentation (PDFs, Markdown documentation, Playwright-scraped web streams, raw text) into memory-bounded, token-quantized chunks with strict anti-prompt injection sanitization and SHA-256 deduplication hashing.

---

## 2. Architecture & File Layout
* `schemas.py`: Pydantic input/output schemas, enum types, chunk models, validation rules.
* `service.py`: Asynchronous document ingestion engine, regex-based security filters, sliding window chunker.
* `router.py`: FastAPI endpoint routes mounted under `/api/v1/ingest`.
* `tests/test_doc_ingestion.py`: Unit and edge-case verification test suite.

---

## 3. Strict 5-Day Mon-Fri Engineering Lifecycle (Anti-AI-Trap)
To maintain engineering rigor and prevent shallow AI submissions, you must follow the 5-day cycle:
* **Day 11 (Monday)**: Mathematical foundations & data contract (`FEATURE_SPEC.md`).
* **Day 12 (Tuesday)**: High-throughput async ingestion engine with backpressure limits.
* **Day 13 (Wednesday)**: Comprehensive edge-case test suite (10+ tests, 60%+ negative test ratio).
* **Day 14 (Thursday)**: High-concurrency load testing & latency profiling (median < 25ms, p95 < 50ms).
* **Day 15 (Friday)**: Diagnostic error analysis memo, operational runbook, and Evidence-Driven PR (EDPR) with Loom demo.

