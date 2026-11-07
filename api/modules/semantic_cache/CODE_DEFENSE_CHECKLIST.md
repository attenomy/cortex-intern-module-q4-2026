# CTX-003 Code Defense Checklist

## 1. Problem and architecture
- [ ] Explain why a semantic cache is needed.
- [ ] Explain exact-query lookup versus semantic lookup.
- [ ] Explain why Redis is used for shared cache storage.
- [ ] Explain the 384-dimensional embedding model.

## 2. Exact-query path
- [ ] Explain query normalization using casefold and whitespace collapsing.
- [ ] Explain SHA-256 exact-query keys.
- [ ] Explain why exact lookup happens before embedding inference.
- [ ] Explain how Lua retrieves the entry and increments hits atomically.

## 3. Semantic path
- [ ] Explain normalized float32 embeddings.
- [ ] Explain Redis VSIM and candidate retrieval.
- [ ] Explain metadata retrieval through a Redis pipeline.
- [ ] Explain cosine similarity and the threshold.
- [ ] Explain why invalid metadata is rejected.

## 4. Storage and expiration
- [ ] Explain vector insertion and metadata storage.
- [ ] Explain the transactional metadata pipeline.
- [ ] Explain vector rollback when metadata writing fails.
- [ ] Explain TTL and stale vector cleanup.

## 5. Reliability and concurrency
- [ ] Explain fail-open lookup behavior.
- [ ] Explain why store failures are propagated.
- [ ] Explain SET NX EX lock acquisition.
- [ ] Explain ownership tokens and atomic Lua lock release.
- [ ] State clearly that lock helpers are not integrated into the main lookup/store flow.

## 6. Performance evidence
- [ ] Explain exact-query concurrency results.
- [ ] Explain semantic-query concurrency results.
- [ ] Identify CPU embedding inference as the main concurrency bottleneck.
- [ ] Explain the difference between median and P95.
- [ ] Explain why exact-query SLA success does not imply semantic-query SLA success.
- [ ] Explain the limitations of the benchmark workload.

## 7. Experiments and limitations
- [ ] Explain that batch encoding was benchmarked but production batching was not implemented.
- [ ] Explain that int8 quantization was simulated in memory only.
- [ ] Explain why native Redis quantization was not enabled.
- [ ] Explain why thread-count experiments need repeatability testing.
- [ ] Explain why tracemalloc results do not prove there are no memory leaks.

## 8. Production safety
- [ ] Confirm no production Redis index migration was performed.
- [ ] Explain why index changes require a separately validated migration.
- [ ] Identify the next steps for semantic concurrency optimization.
