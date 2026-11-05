# FEATURE SPECIFICATION
## CTX-003: Redis Semantic Vector Caching & Query Deduplication Engine

**Project:** Attenomy Cortex  
**Engineer:** Yakshith Anandapu (@YAKSHITH684)  
**Ticket:** CTX-003  
**Module:** `api/modules/semantic_cache/`  
**Branch:** `feature/CTX-003-semantic-cache`  
**Target Branch:** `staging`  
**Status:** Proposed – Pending Review

---

## 1. Objective

Develop a Redis-backed semantic caching system that identifies identical and semantically similar incoming queries and retrieves previously cached responses instead of repeating expensive neural inference computations.

The system must provide efficient vector similarity search, reliable cache retrieval, duplicate request handling, and graceful recovery when Redis is unavailable.

## 2. Existing Architecture

The current module contains:

- `router.py` – FastAPI endpoints for cache lookup and statistics.
- `schemas.py` – Pydantic request and response models.
- `service.py` – Existing local dictionary-based cache implementation.
- `tests/test_semantic_cache.py` – Initial API tests.

The existing service supports exact normalized-query matching but does not yet implement Redis connectivity or semantic vector search.

## 3. Proposed System Architecture

The proposed request lifecycle:

1. Receive an incoming query through the FastAPI endpoint.
2. Validate the request using Pydantic.
3. Normalize the query.
4. Generate its embedding using the configured embedding model.
5. Search the Redis vector index using cosine similarity.
6. Compare the similarity score against the configured threshold.
7. If similarity is at least 0.95, retrieve and return the cached response.
8. If no suitable match exists, return a cache miss so the application can perform live inference.
9. Store the generated response and its embedding after successful inference.
10. If Redis becomes unavailable, fail open and allow live inference.

## 4. Redis Data Structures and Key Design

**Backend:** Redis with vector search support.

Proposed Redis key:

`semantic_cache:{entry_id}`

Each cache entry should contain:

| Field | Description |
|---|---|
| entry_id | Unique cache entry identifier |
| query | Original query |
| normalized_query | Normalized query |
| embedding | Query embedding vector |
| payload | Cached response |
| created_at | Entry creation timestamp |
| expires_at | Expiration timestamp |

**Vector index requirements:**

- Use cosine similarity.
- Support nearest-neighbour vector search.
- Configure vector dimensions according to the selected embedding model.
- Use an appropriate Redis vector index strategy.
- Avoid storing duplicate entries unnecessarily.

The embedding model and vector dimensions must be configurable rather than hardcoded.

## 5. Pydantic Data Contracts

### 5.1 CacheLookupRequest

Existing fields:

| Field | Type | Validation |
|---|---|---|
| query | str | Required, non-empty |
| threshold | float | Default 0.95, minimum 0.5, maximum 1.0 |

### 5.2 Proposed CacheStoreRequest

| Field | Type | Validation |
|---|---|---|
| query | str | Required, non-empty |
| payload | Dict[str, Any] | Required |
| ttl_seconds | Optional[int] | Positive when provided |

### 5.3 CacheLookupResponse

Existing fields:

| Field | Type |
|---|---|
| hit | bool |
| matched_query | Optional[str] |
| similarity_score | Optional[float] |
| cached_payload | Optional[Dict[str, Any]] |
| latency_ms | float |

### 5.4 CacheStatsResponse

| Field | Type |
|---|---|
| total_entries | int |
| hit_rate | float |
| redis_connected | bool |

All request models must enforce appropriate validation and reject malformed inputs.

## 6. Semantic Similarity and Deduplication

The system will use vector embeddings to represent query meaning.

Similarity will be calculated using cosine similarity:

`similarity(A, B) = (A · B) / (||A|| × ||B||)`

Decision logic:

- Similarity >= 0.95: Cache hit.
- Similarity < 0.95: Cache miss.
- Invalid or zero-length vectors: Reject or safely handle as an invalid embedding.
- Identical normalized queries: Support exact-match optimization.

The similarity threshold must remain configurable within the validation range.

## 7. Cache Expiration and Invalidation

Each cache entry should support a configurable TTL.

Requirements:

- Assign an expiration time when storing an entry.
- Automatically expire entries after their TTL.
- Prevent expired entries from being returned.
- Support invalidation of stale or corrupted entries.
- Avoid permanent accumulation of unused cache records.

The default TTL must be finalized during implementation review.

## 8. Concurrency and Thread Safety

The implementation must support concurrent cache operations.

Proposed mechanisms:

- Use Redis connection pooling.
- Use atomic Redis operations where appropriate.
- Use Redis locks or an equivalent atomic coordination mechanism for duplicate request suppression.
- Avoid unsafe shared mutable Python state.
- Ensure concurrent requests do not corrupt cache entries.
- Apply bounded waiting when another request is already computing the same result.

## 9. Redis Failure Handling

The system must implement fail-open resilience.

Failure scenarios include:

- Redis server unavailable.
- Connection timeout.
- Network interruption.
- Authentication failure.
- Redis command failure.
- Malformed cached response.

Expected behaviour:

1. Detect Redis connection and operation failures.
2. Record the failure using appropriate logging.
3. Avoid exposing internal Redis exceptions to API clients.
4. Treat unavailable cache data as a cache miss.
5. Allow live neural inference to continue.
6. Attempt reconnection using bounded retry or reconnect behaviour.
7. Avoid retry loops that increase request latency.

Redis failure must not independently cause an HTTP 500 response.

## 10. Negative and Boundary Test Scenarios

The following failure conditions must be covered.

| ID | Scenario | Expected behaviour |
|---|---|---|
| N01 | Empty query | Reject request |
| N02 | Whitespace-only query | Reject request |
| N03 | Missing query field | Pydantic validation error |
| N04 | Query supplied as integer | Reject invalid type |
| N05 | Threshold below 0.5 | Reject request |
| N06 | Threshold above 1.0 | Reject request |
| N07 | Malformed embedding | Handle safely |
| N08 | Embedding dimension mismatch | Reject or safely handle |
| N09 | Zero-length embedding vector | Prevent invalid similarity calculation |
| N10 | Redis connection unavailable | Fail open |
| N11 | Redis operation timeout | Fall back to live inference |
| N12 | Corrupted cached JSON payload | Reject corrupted entry safely |
| N13 | Expired cache entry | Treat as cache miss |
| N14 | Duplicate concurrent requests | Prevent unsafe duplicate writes |
| N15 | Empty or malformed cache payload | Reject invalid data |

## 11. Testing Strategy

The implementation must contain at least 12–15 unit and integration tests.

Testing categories:

- Request validation.
- Semantic similarity calculation.
- Cache hit and miss.
- Redis connectivity.
- Cache expiration.
- Concurrent requests.
- Error recovery.
- Statistics accuracy.
- Invalid vector handling.

**Mandatory defensive testing requirement:**

More than 60% of all tests must cover negative and boundary conditions.

All tests must pass before the pull request is submitted.

## 12. Performance Requirements

The implementation must satisfy the following module-specific and cohort-wide requirements.

| Metric | Target |
|---|---|
| Cache hit latency | Strictly below 5 ms |
| CPU median latency | Below 25 ms |
| CPU p95 latency | Below 50 ms |
| Defensive test ratio | Greater than 60% |
| Memory profiling | 5,000 requests |
| Memory leaks | Zero observed leaks |

Latency must be measured using actual execution rather than simulated values.

Measurements should distinguish Redis lookup time, embedding generation time, and total request latency.

## 13. Performance Tuning

At least six experiments must be performed.

Proposed tuning dimensions:

1. Different similarity thresholds.
2. Different vector index configurations.
3. Different batch sizes.
4. Different Redis connection pool sizes.
5. Different cache TTL values.
6. Different concurrency levels.

Document results in:

`reports/tuning_experiments.md`

Use `cProfile` and an appropriate load-testing approach to collect performance evidence.

## 14. Proposed Module Structure

```text
api/
└── modules/
    └── semantic_cache/
        ├── README.md
        ├── FEATURE_SPEC.md
        ├── __init__.py
        ├── router.py
        ├── schemas.py
        ├── service.py
        └── tests/
            └── test_semantic_cache.py
```

Additional reporting files will be created as required during implementation.

## 15. Acceptance Criteria

- Redis vector search is implemented.
- Cosine similarity matching works correctly.
- Similarity threshold is configurable.
- Pydantic validation is enforced.
- Cache hits return stored responses.
- Cache misses allow live inference.
- Duplicate requests are handled safely.
- TTL and invalidation work correctly.
- Redis failures do not interrupt live inference.
- Thread-safe concurrent operations are supported.
- At least 12–15 tests pass.
- More than 60% of tests cover negative and boundary conditions.
- Performance targets are measured and documented.
- Operational documentation and evidence-driven PR are prepared.

## 16. Review Questions / Decisions Requiring Confirmation

Before implementation, confirm:

1. Which embedding model and vector dimensions should be used?
2. Is Redis Stack available in the development and evaluation environments?
3. What is the approved default cache TTL?
4. Should embedding generation be handled inside this module or by an existing Cortex service?
5. Should cache storage be exposed through a new endpoint or integrated into the existing inference workflow?
6. What is the expected cache payload format?

---

**Prepared by:** Yakshith Anandapu  
**Ticket:** CTX-003  
**Review status:** Awaiting Lead / CPO approval  
**Implementation status:** Not started – specification-first phase.
