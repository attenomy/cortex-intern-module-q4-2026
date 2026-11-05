# ADR-001: Redis-Backed Semantic Cache

- **Status:** Implemented; performance validation ongoing
- **Date:** 2026-11-05
- **Scope:** Attenomy Cortex CTX-003

## 1. Context

The service needs to reduce repeated inference and response-generation work by reusing cached results for identical or semantically similar queries.

The implementation uses Redis for vector search and metadata storage, with a CPU-based Sentence Transformers model for query embeddings.

## 2. Decision

Use a Redis-backed cache with two lookup paths:

1. An exact-query fast path using a normalized query hash.
2. A semantic fallback using normalized embeddings and Redis vector search.

The embedding model is `sentence-transformers/all-MiniLM-L6-v2`, configured for 384-dimensional vectors.

## 3. Architecture

### Query normalization

Queries are normalized using case folding and whitespace normalization:

- Convert to lowercase-equivalent form using `casefold()`.
- Collapse repeated whitespace.
- Generate a SHA-256 hash of the normalized query.

The hash is used for exact-query keys and query-lock keys.

### Exact-query lookup

The service checks the exact-query key before generating an embedding.

A Lua script retrieves the cached entry and increments the hit counter atomically. An exact match returns similarity score 1.0 without model inference.

### Semantic lookup

On an exact miss:

1. Generate a normalized float32 query embedding.
2. Execute Redis `VSIM` against the configured vector set.
3. Retrieve candidate metadata using a non-transactional pipeline.
4. Validate metadata, payload, embedding dimensions and finite values.
5. Calculate cosine similarity against candidate embeddings.
6. Compare the best score against the configured threshold.
7. Update hit or miss counters.

The current lookup threshold default is 0.95.

### Storage

The store operation validates the query, payload and TTL, generates an embedding, and adds the vector to Redis.

It then writes metadata and the exact-query mapping through a transactional pipeline. If metadata writing fails, the vector insertion is rolled back with `VREM`.

### Expiration and metadata

Cache entries and exact-query mappings use Redis TTLs. Lookup also detects invalid or missing metadata and attempts to remove stale vector IDs.

## 4. Redis key layout

- Vector set: `semantic_cache:vectors`
- Entry metadata: `semantic_cache:entry:<uuid>`
- Exact-query mapping: `semantic_cache:exact:<sha256>`
- Query lock: `semantic_cache:lock:<sha256>`
- Hit counter: `semantic_cache:stats:hits`
- Miss counter: `semantic_cache:stats:misses`

Default cache TTL: 3600 seconds.

## 5. Failure handling

Lookup is designed to fail open: Redis or lookup errors return a cache miss so the caller can continue without a cache hit.

Store errors are propagated after connection state is updated. A failed metadata pipeline attempts to remove the vector that was already inserted.

The service validates embedding dimensions and rejects non-finite embedding values.

## 6. Distributed query locking

The service implements lock helpers using Redis `SET NX EX`, unique ownership tokens and an atomic Lua release script.

The context manager releases an acquired lock in its `finally` block. Lock acquisition and release failures fall back without blocking inference.

**Integration limitation:** Repository search confirms that the lock helpers are referenced by their tests but are not currently called by the main lookup/store flow. Therefore, the current cache flow must not be described as providing active request-level duplicate-work suppression.

## 7. Alternatives considered

- **Exact-query-only cache:** Lower lookup overhead, but does not reuse results for paraphrased queries.
- **Application-memory cache:** Avoids Redis calls but does not provide shared cache state across service processes.
- **Always run semantic search:** Supports related queries but adds embedding and vector-search latency even for exact repeats.

The selected hybrid design provides a fast exact path and a semantic fallback.

## 8. Performance evidence

Measurements were collected on the local development environment. They are workload- and machine-specific.

### Exact-query concurrency

| Workers | Requests | Median (ms) | P95 (ms) |
|---:|---:|---:|---:|
| 1 | 100 | 0.42 | 0.713 |
| 4 | 400 | 1.12 | 1.985 |
| 8 | 800 | 2.216 | 4.458 |
| 16 | 1600 | 4.382 | 9.329 |

The tested exact-query workloads met the median <25 ms and P95 <50 ms targets.

### Semantic-query concurrency

| Workers | Requests | Median (ms) | P95 (ms) |
|---:|---:|---:|---:|
| 1 | 20 | 10.650 | 14.963 |
| 4 | 80 | 104.851 | 130.431 |
| 8 | 160 | 176.297 | 280.231 |
| 16 | 320 | 236.168 | 555.633 |

Semantic cache hits were returned in these tests, but the latency targets were not met at 4, 8 or 16 workers.

Profiling indicates CPU embedding inference is the primary bottleneck under concurrency, with Redis work contributing additional latency.

## 9. Experiments and limitations

- Batch encoding experiments were performed, but production request micro-batching was not implemented.
- Int8 quantization was simulated in memory; native Redis quantization was not benchmarked or enabled through a migration.
- VSIM candidate-count tuning was not completed.
- Semantic concurrency used one stored query and one related query.
- Thread-count comparisons were individual runs and require repeatability testing.
- Memory profiling does not formally prove the absence of memory leaks.
- Results depend on the machine, model, Redis version and workload.

See `reports/tuning_experiments.md` and the Day 14 benchmark reports for detailed measurements.

## 10. Production safety

Do not change the production Redis index without a separately validated migration.

No production index migration is part of this decision record. Benchmark results are not sufficient evidence to change the production index configuration.

## 11. Follow-up work

- Integrate distributed locking into the request flow only after defining and testing its lifecycle and concurrency behavior.
- Investigate CPU embedding contention and repeat concurrency benchmarks.
- Evaluate production batching separately from offline batch-encoding experiments.
- Validate any Redis index configuration change through a separate migration plan.
