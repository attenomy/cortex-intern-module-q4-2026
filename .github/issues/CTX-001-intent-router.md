# [CTX-001] Neural Semantic Intent Router & Sub-50ms CPU Inference Engine

**Assignee**: Abhishek Adbhute (`@abhishekadbhute-create`)  
**Target Module**: `api/modules/intent_router/`  
**Target Branch**: `feature/CTX-001-intent-router` -> `staging`  
**SLA / Latency Target**: p95 inference latency < 50ms on CPU  

---

## 1. Problem Statement
The current intent router (`api/modules/intent_router/service.py`) relies on static keyword matching and a simulated delay. It cannot disambiguate complex queries, multi-intent phrases, or unseen vocabulary.

## 2. Deliverables & Technical Scope
1. **Fine-Tuned Model / ONNX Pipeline**: Fine-tune `DistilBERT` or `all-MiniLM-L6-v2` (or export to ONNX runtime) on query classification.
2. **Pre-Warmed Lifecycle**: Initialize and warm up model weights during FastAPI startup to avoid cold starts.
3. **Deterministic Fallback**: Return fallback category `search` when highest confidence is `< 0.60`.
4. **Unit Tests**: Minimum 6 unit and negative tests in `api/modules/intent_router/tests/test_intent_router.py`.
5. **Profiling Evidence**: cProfile / Locust test verifying median latency `< 25ms` and p95 `< 50ms`.

## 3. Pull Request Submission
* Open PR to `staging` using `.github/PULL_REQUEST_TEMPLATE.md`.
* Include terminal pytest output and 60-90s demo video link.
