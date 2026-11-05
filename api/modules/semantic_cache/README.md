# Module: Semantic Cache (`api/modules/semantic_cache/`)

> **Assigned Engineer**: Yakshith Anandapu (`@YAKSHITH684`)  
> **Ticket**: `[CTX-003]` Redis Semantic Vector Caching & Query Deduplication Engine  
> **Target Branch**: `feature/CTX-003-semantic-cache` -> `staging`  

---

## Module Overview
The Semantic Cache module intercepts inbound query prompts and routes, checking against a Redis vector store. If cosine similarity exceeds 0.95, it returns the cached response in `< 5ms`, avoiding redundant inference computations.

## Key Constraints
- **Latency Budget**: Cache hit latency strictly `< 5ms`.
- **Backend**: Redis vector search with cosine similarity indexing.
- **Fail-Open Resilience**: If Redis connection is unreachable, gracefully fall back to live neural inference without throwing 500 errors.

## Testing
Run unit tests for this module:
```bash
pytest modules/semantic_cache/tests/ -v
```

