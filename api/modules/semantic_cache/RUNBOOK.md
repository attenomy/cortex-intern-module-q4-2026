# Attenomy Cortex - Semantic Cache Runbook

**Module:** `api/modules/semantic_cache/`
**Ticket:** CTX-003 - Redis Semantic Vector Caching
**Branch:** `feature/CTX-003-semantic-cache-clean`

## 1. Overview

The Semantic Cache uses Sentence Transformer embeddings and Redis vector search to identify previously cached queries.

Features:
- Normalized exact-query lookup.
- Semantic similarity lookup.
- Configurable similarity threshold and TTL.
- Cache statistics.
- Fail-open lookup behavior.
- Distributed locking.
- Startup model warm-up and Redis client cleanup.

Exact-query and semantic lookup have different latency characteristics. Exact-query benchmark results must not be presented as semantic lookup results.

## 2. Prerequisites

- Ubuntu WSL.
- Python 3.14.4 (tested environment).
- Virtual environment: `api/.venv-wsl/`.
- Redis 8 with vector-set command support.
- Module dependencies from `api/modules/semantic_cache/requirements.txt`.

Docker is not required for this local workflow.


## 3. Start and verify Redis

Start Redis using `sudo service redis-server start`.

Verify connectivity using `redis-cli ping`. The expected response is `PONG`.

The default Redis URL is `redis://localhost:6379/0`.

## 4. Configuration

| Variable | Default | Purpose |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `SEMANTIC_CACHE_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `SEMANTIC_CACHE_DIMENSIONS` | `384` | Embedding dimensions |
| `SEMANTIC_CACHE_TTL_SECONDS` | `3600` | Default entry TTL |
| `SEMANTIC_CACHE_LOCK_TTL_SECONDS` | `30` | Lock TTL |
| `SEMANTIC_CACHE_LOCK_WAIT_SECONDS` | `2` | Lock wait duration |
| `SEMANTIC_CACHE_LOCK_POLL_SECONDS` | `0.05` | Lock polling interval |

The Sentence Transformer model may need to download on first use. Startup warm-up attempts to load the model before requests are served.

## 5. Start the FastAPI application

From the project root, enter the API directory using `cd api`.

Activate the WSL virtual environment with `source .venv-wsl/bin/activate`.

Start the application with `PYTHONPATH=. python -m uvicorn main:app --host 0.0.0.0 --port 8000`.

Open the interactive API documentation at `http://localhost:8000/docs`.

## 6. API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/cache/store` | Store a query and payload |
| POST | `/api/v1/cache/lookup` | Find an exact or semantically similar cached query |
| GET | `/api/v1/cache/stats` | Retrieve cache statistics |

Blank queries are rejected with HTTP 400. Store failures may return HTTP 400 or 503 depending on the error.

## 7. Operational checks

- Confirm Redis responds to `redis-cli ping`.
- Confirm the FastAPI application starts without import or connection errors.
- Use `/docs` to exercise the store, lookup and stats endpoints.
- Check the `redis_connected` field in the stats response.
- Review `api/modules/semantic_cache/reports/` for benchmark JSON, Markdown and profiling evidence.

## 8. Performance findings and limitations

- Exact-query lookup passed the measured median and p95 targets of 25 ms and 50 ms in the Day 14 concurrency tests.
- Semantic lookup passed at one worker, but failed the p95 target at 4, 8 and 16 workers.
- CPU embedding generation was the primary semantic-concurrency bottleneck; Redis search was a secondary contributor.
- Batch encoding and int8 quantization were experimental benchmarks, not production features.
- Quantization measurements used an in-memory simulation, not a Redis index migration.
- Results depend on the test machine, model, Redis instance and workload.

## 9. Production safety

Do not change the production Redis index without a separately validated migration. Do not claim that high-concurrency semantic lookup meets the latency SLA based on exact-query results.
