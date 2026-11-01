# [CTX-002] Cognitive Document Entity Extractor & Layout Classifier

**Assignee**: Abhinav Singh (`@Abhinav55849`)  
**Target Module**: `api/modules/doc_extractor/`  
**Target Branch**: `feature/CTX-002-doc-extractor` -> `staging`  
**SLA / Quality Target**: Layout classification macro F1 > 0.90; schema validation  

---

## 1. Problem Statement
The `/api/v1/extract` endpoint in `api/modules/doc_extractor/service.py` currently returns a mocked JSON dictionary. It does not parse incoming documents, validate entity schemas, or handle corrupted base64 images.

## 2. Deliverables & Technical Scope
1. **Multimodal Layout Model**: Implement a fine-tuned layout classifier (`MobileNetV3` or document feature extractor).
2. **Schema Validator**: Enforce structured invoice entity extraction (`vendor_name`, `invoice_number`, `net_amount`, `currency`).
3. **Defensive Error Handling**: Catch corrupted or empty payloads and return clean HTTP 422 errors instead of 500 server crashes.
4. **Unit Tests**: Minimum 5 unit and edge-case tests in `api/modules/doc_extractor/tests/test_doc_extractor.py`.
5. **Profiling Evidence**: Document extraction latency benchmark under load.

## 3. Pull Request Submission
* Open PR to `staging` using `.github/PULL_REQUEST_TEMPLATE.md`.
* Include terminal pytest output and 60-90s demo video link.

