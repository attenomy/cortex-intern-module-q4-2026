# [CTX-003] Redis Semantic Vector Caching & Query Deduplication Engine

**Assignee**: Yakshith Anandapu (`@YAKSHITH684`)  
**Target Module**: `api/modules/semantic_cache/`  
**Target Branch**: `feature/CTX-003-semantic-cache` -> `staging`  
**SLA / Latency Target**: Cache hit latency strictly < 5.0ms; > 50% duplicate avoidance  

---

## 1. Problem Statement
Every inbound query currently triggers neural inference or database lookup even when semantically identical queries were recently answered. This burns CPU cycles and increases average response latency.

## 2. Deliverables & Technical Scope
1. **Redis Vector Cache Service**: Implement `api/modules/semantic_cache/service.py` with cosine similarity lookup over query embeddings.
2. **Hit SLA**: Queries with cosine similarity > 0.95 return cached decisions in `< 5ms`.
3. **Fail-Open Resilience**: If Redis container disconnects, log a warning and fall back to live neural inference without raising 500 errors.
4. **Unit Tests**: Minimum 5 unit and edge-case tests in `api/modules/semantic_cache/tests/test_semantic_cache.py`.
5. **Profiling Evidence**: Benchmarked cache hit vs cache miss latency output.

## 3. Pull Request Submission
* Open PR to `staging` using `.github/PULL_REQUEST_TEMPLATE.md`.
* Include terminal pytest output and 60-90s demo video link.

