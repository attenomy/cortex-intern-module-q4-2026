# Module: Semantic Cache (`api/modules/semantic_cache/`)

> **Assigned Engineer**: Yakshith Anandapu (`@YAKSHITH684`)
> **Ticket**: `[CTX-003]` Redis Semantic Vector Caching & Query Deduplication Engine
> **Target Branch**: `feature/CTX-003-semantic-cache-clean` -> `staging`

---

## Module Overview
The Semantic Cache module intercepts inbound query prompts and routes, checking against a Redis vector store. Semantic lookup latency depends on CPU embedding inference and concurrency. Recorded benchmarks exceed the 50 ms P95 target at 4, 8, and 16 workers.

## Key Constraints
- **Latency Budget**: Exact-query and semantic-query paths have different latency profiles. See benchmark reports for measured results.
- **Backend**: Redis vector search with cosine similarity indexing.
- **Fail-Open Resilience**: If Redis connection is unreachable, gracefully fall back to live neural inference without throwing 500 errors.

## Testing
Run unit tests for this module:
```bash
pytest modules/semantic_cache/tests/ -v
```

