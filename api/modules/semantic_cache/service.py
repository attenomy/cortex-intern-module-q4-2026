
import hashlib
import json
import os
import secrets
import threading
import time
import uuid

from contextlib import contextmanager
from typing import Any, Dict, Optional, Iterator

import numpy as np
import redis


class SemanticCacheService:
    """Redis-backed semantic cache with distributed query locking."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )

        self.model_name = os.getenv(
            "SEMANTIC_CACHE_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.dimensions = int(
            os.getenv("SEMANTIC_CACHE_DIMENSIONS", "384")
        )

        self.default_ttl = int(
            os.getenv("SEMANTIC_CACHE_TTL_SECONDS", "3600")
        )

        self.lock_ttl = int(
            os.getenv("SEMANTIC_CACHE_LOCK_TTL_SECONDS", "30")
        )

        self.lock_wait_timeout = float(
            os.getenv("SEMANTIC_CACHE_LOCK_WAIT_SECONDS", "2")
        )

        self.lock_poll_interval = float(
            os.getenv("SEMANTIC_CACHE_LOCK_POLL_SECONDS", "0.05")
        )

        if self.lock_ttl <= 0:
            raise ValueError("Lock TTL must be positive.")

        if self.lock_wait_timeout < 0:
            raise ValueError("Lock wait timeout cannot be negative.")

        if self.lock_poll_interval <= 0:
            raise ValueError("Lock polling interval must be positive.")

        self.vector_key = "semantic_cache:vectors"
        self.entry_prefix = "semantic_cache:entry:"
        self.exact_prefix = "semantic_cache:exact:"
        self.lock_prefix = "semantic_cache:lock:"

        self.hits_key = "semantic_cache:stats:hits"
        self.misses_key = "semantic_cache:stats:misses"

        self.is_connected = False
        self._model = None
        self._model_lock = threading.Lock()

        self.redis_client = redis.Redis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
            retry_on_timeout=False,
            health_check_interval=30
        )

    # --------------------------------------------------
    # QUERY NORMALIZATION
    # --------------------------------------------------

    @staticmethod
    def _normalize_query(query: str) -> str:
        return " ".join(query.casefold().split())

    def _query_hash(self, query: str) -> str:
        normalized = self._normalize_query(query)

        return hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

    def _exact_key(self, query: str) -> str:
        return self.exact_prefix + self._query_hash(query)

    def _lock_key(self, query: str) -> str:
        return self.lock_prefix + self._query_hash(query)

    # --------------------------------------------------
    # DISTRIBUTED QUERY LOCKING
    # --------------------------------------------------

    def acquire_query_lock(
        self,
        query: str,
        ttl_seconds: Optional[int] = None,
        wait_timeout_seconds: Optional[float] = None,
        poll_interval_seconds: Optional[float] = None
    ) -> Optional[str]:
        """
        Acquire a distributed Redis lock for a normalized query.

        Returns:
            Unique ownership token if acquired.
            None if the lock is unavailable or Redis fails.

        Redis SET NX EX provides atomic lock acquisition.
        """

        normalized = self._normalize_query(query)

        if not normalized:
            raise ValueError("Query cannot be empty.")

        ttl = (
            self.lock_ttl
            if ttl_seconds is None
            else ttl_seconds
        )

        wait_timeout = (
            self.lock_wait_timeout
            if wait_timeout_seconds is None
            else wait_timeout_seconds
        )

        poll_interval = (
            self.lock_poll_interval
            if poll_interval_seconds is None
            else poll_interval_seconds
        )

        if ttl <= 0:
            raise ValueError("Lock TTL must be positive.")

        if wait_timeout < 0:
            raise ValueError("Wait timeout cannot be negative.")

        if poll_interval <= 0:
            raise ValueError("Poll interval must be positive.")

        lock_key = self._lock_key(normalized)
        ownership_token = secrets.token_urlsafe(32)

        deadline = time.monotonic() + wait_timeout

        while True:
            try:
                acquired = self.redis_client.set(
                    lock_key,
                    ownership_token,
                    nx=True,
                    ex=ttl
                )

                self.is_connected = True

                if acquired:
                    return ownership_token

            except Exception:
                # Fail open: inference can continue without a lock.
                self.is_connected = False
                return None

            remaining = deadline - time.monotonic()

            if remaining <= 0:
                return None

            time.sleep(
                min(poll_interval, remaining)
            )

    def release_query_lock(
        self,
        query: str,
        ownership_token: str
    ) -> bool:
        """
        Release a lock only when the supplied token owns it.

        Lua makes ownership verification and deletion atomic.
        """

        normalized = self._normalize_query(query)

        if not normalized or not ownership_token:
            return False

        lock_key = self._lock_key(normalized)

        release_script = """
            if redis.call('GET', KEYS[1]) == ARGV[1] then
                return redis.call('DEL', KEYS[1])
            end

            return 0
        """

        try:
            result = self.redis_client.execute_command(
                "EVAL",
                release_script,
                1,
                lock_key,
                ownership_token
            )

            self.is_connected = True

            return int(result or 0) == 1

        except Exception:
            # An expired lock will eventually disappear through TTL.
            self.is_connected = False
            return False

    @contextmanager
    def query_lock(
        self,
        query: str,
        ttl_seconds: Optional[int] = None,
        wait_timeout_seconds: Optional[float] = None,
        poll_interval_seconds: Optional[float] = None
    ) -> Iterator[bool]:
        """
        Context manager for distributed query coordination.

        The yielded value is True when the lock is acquired.

        False means the caller should continue in fail-open mode.
        """

        token = self.acquire_query_lock(
            query=query,
            ttl_seconds=ttl_seconds,
            wait_timeout_seconds=wait_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds
        )

        acquired = token is not None

        try:
            yield acquired

        finally:
            if acquired:
                self.release_query_lock(
                    query,
                    token
                )

    # --------------------------------------------------
    # EMBEDDING MODEL
    # --------------------------------------------------

    def _get_model(self):
        """Load the embedding model only when required."""

        if self._model is None:
            with self._model_lock:
                if self._model is None:

                    from sentence_transformers import SentenceTransformer

                    model = SentenceTransformer(
                        self.model_name,
                        device="cpu"
                    )

                    if (
                        model.get_embedding_dimension()
                        != self.dimensions
                    ):
                        raise ValueError(
                            "Embedding dimension does not match configuration."
                        )

                    self._model = model

        return self._model

    def _embed(self, query: str) -> np.ndarray:
        """Generate and validate a normalized embedding."""

        model = self._get_model()

        vector = model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        vector = np.asarray(
            vector,
            dtype=np.float32
        )

        if vector.shape != (self.dimensions,):
            raise ValueError("Invalid embedding dimensions.")

        if not np.all(np.isfinite(vector)):
            raise ValueError("Embedding contains invalid values.")

        return vector

    # --------------------------------------------------
    # EMPTY RESULT
    # --------------------------------------------------

    def _empty_result(
        self,
        latency_ms: float,
        embedding_latency_ms: float = 0.0,
        redis_latency_ms: float = 0.0,
        timings: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:

        result = {
            "hit": False,
            "matched_query": None,
            "similarity_score": 0.0,
            "cached_payload": None,
            "latency_ms": latency_ms,
            "embedding_latency_ms": embedding_latency_ms,
            "redis_latency_ms": redis_latency_ms
        }

        if timings is not None:
            result["timings"] = timings

        return result

    # --------------------------------------------------
    # CACHE LOOKUP
    # --------------------------------------------------

    def lookup(
        self,
        query: str,
        threshold: float = 0.95
    ) -> Dict[str, Any]:

        started = time.perf_counter()

        timings = {
            "exact_lookup_ms": 0.0,
            "vsim_ms": 0.0,
            "metadata_pipeline_ms": 0.0,
            "similarity_calculation_ms": 0.0,
            "counter_update_ms": 0.0,
            "cleanup_ms": 0.0
        }

        embedding_latency_ms = 0.0
        redis_latency_ms = 0.0

        try:
            query = query.strip()

            if not query:
                return self._empty_result(
                    0.0,
                    timings=timings
                )

            # STEP 1: Exact-query lookup.

            exact_key = self._exact_key(query)

            exact_script = """
                local value = redis.call('GET', KEYS[1])

                if value then
                    redis.call('INCR', KEYS[2])
                end

                return value
            """

            stage_started = time.perf_counter()

            exact_json = self.redis_client.execute_command(
                "EVAL",
                exact_script,
                2,
                exact_key,
                self.hits_key
            )

            timings["exact_lookup_ms"] = round(
                (time.perf_counter() - stage_started) * 1000,
                3
            )

            self.is_connected = True

            if exact_json is not None:
                metadata = json.loads(exact_json)

                elapsed_ms = round(
                    (time.perf_counter() - started) * 1000,
                    3
                )

                return {
                    "hit": True,
                    "matched_query": metadata["query"],
                    "similarity_score": 1.0,
                    "cached_payload": metadata["payload"],
                    "latency_ms": elapsed_ms,
                    "embedding_latency_ms": 0.0,
                    "redis_latency_ms": timings["exact_lookup_ms"],
                    "timings": timings
                }

            # STEP 2: Generate query embedding.

            stage_started = time.perf_counter()

            query_vector = self._embed(query)

            embedding_latency_ms = round(
                (time.perf_counter() - stage_started) * 1000,
                3
            )

            # STEP 3: Prepare Redis VSIM command.

            vector_values = [
                str(float(value))
                for value in query_vector
            ]

            command = [
                "VSIM",
                self.vector_key,
                "VALUES",
                str(self.dimensions),
                *vector_values,
                "COUNT",
                "20",
                "WITHSCORES"
            ]

            # STEP 4: Execute vector similarity search.

            stage_started = time.perf_counter()

            results = self.redis_client.execute_command(
                *command
            )

            timings["vsim_ms"] = round(
                (time.perf_counter() - stage_started) * 1000,
                3
            )

            entry_ids = [
                results[position].decode()
                if isinstance(results[position], bytes)
                else str(results[position])
                for position in range(0, len(results), 2)
            ]

            # STEP 5: Fetch metadata using one pipeline.

            metadata_jsons = []

            stage_started = time.perf_counter()

            if entry_ids:
                with self.redis_client.pipeline(
                    transaction=False
                ) as pipe:

                    for entry_id in entry_ids:
                        pipe.get(
                            self.entry_prefix + entry_id
                        )

                    metadata_jsons = pipe.execute()

            timings["metadata_pipeline_ms"] = round(
                (time.perf_counter() - stage_started) * 1000,
                3
            )

            # STEP 6: Validate metadata and calculate similarity.

            best_match = None
            best_score = 0.0
            expired_ids = []

            stage_started = time.perf_counter()

            for entry_id, metadata_json in zip(
                entry_ids,
                metadata_jsons
            ):

                try:
                    if metadata_json is None:
                        expired_ids.append(entry_id)
                        continue

                    metadata = json.loads(metadata_json)

                    if not isinstance(metadata, dict):
                        raise ValueError(
                            "Invalid cache metadata."
                        )

                    cached_vector = np.asarray(
                        metadata["embedding"],
                        dtype=np.float32
                    )

                    if cached_vector.shape != (
                        self.dimensions,
                    ):
                        raise ValueError(
                            "Invalid cached vector dimensions."
                        )

                    if not np.all(np.isfinite(cached_vector)):
                        raise ValueError(
                            "Cached vector contains invalid values."
                        )

                    if not isinstance(
                        metadata.get("payload"),
                        dict
                    ):
                        raise ValueError(
                            "Invalid cached payload."
                        )

                    if not isinstance(
                        metadata.get("query"),
                        str
                    ):
                        raise ValueError(
                            "Invalid cached query."
                        )

                    cosine_score = float(
                        np.dot(
                            query_vector,
                            cached_vector
                        )
                    )

                    cosine_score = max(
                        -1.0,
                        min(1.0, cosine_score)
                    )

                    if cosine_score > best_score:
                        best_score = cosine_score
                        best_match = metadata

                except (
                    ValueError,
                    TypeError,
                    KeyError,
                    OverflowError
                ):
                    expired_ids.append(entry_id)
                    continue

            timings["similarity_calculation_ms"] = round(
                (time.perf_counter() - stage_started) * 1000,
                3
            )

            # STEP 7: Remove expired or invalid vectors.

            stage_started = time.perf_counter()

            if expired_ids:
                self.redis_client.execute_command(
                    "VREM",
                    self.vector_key,
                    *expired_ids
                )

            timings["cleanup_ms"] = round(
                (time.perf_counter() - stage_started) * 1000,
                3
            )

            # STEP 8: Update hit/miss counters.

            stage_started = time.perf_counter()

            if (
                best_match is not None
                and best_score >= threshold
            ):
                self.redis_client.incr(
                    self.hits_key
                )
                hit = True

            else:
                self.redis_client.incr(
                    self.misses_key
                )
                hit = False

            timings["counter_update_ms"] = round(
                (time.perf_counter() - stage_started) * 1000,
                3
            )

            self.is_connected = True

            redis_latency_ms = round(
                timings["exact_lookup_ms"]
                + timings["vsim_ms"]
                + timings["metadata_pipeline_ms"]
                + timings["cleanup_ms"]
                + timings["counter_update_ms"],
                3
            )

            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                3
            )

            if hit:
                return {
                    "hit": True,
                    "matched_query": best_match["query"],
                    "similarity_score": round(
                        best_score,
                        6
                    ),
                    "cached_payload": best_match["payload"],
                    "latency_ms": elapsed_ms,
                    "embedding_latency_ms": embedding_latency_ms,
                    "redis_latency_ms": redis_latency_ms,
                    "timings": timings
                }

            return self._empty_result(
                elapsed_ms,
                embedding_latency_ms,
                redis_latency_ms,
                timings
            )

        except Exception:
            self.is_connected = False

            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                3
            )

            return self._empty_result(
                elapsed_ms,
                embedding_latency_ms,
                redis_latency_ms,
                timings
            )

    # --------------------------------------------------
    # STORE CACHE ENTRY
    # --------------------------------------------------

    def store(
        self,
        query: str,
        payload: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> None:

        query = query.strip()

        if not query:
            raise ValueError(
                "Query cannot be empty."
            )

        if not isinstance(payload, dict) or not payload:
            raise ValueError(
                "Payload must be a non-empty dictionary."
            )

        ttl = (
            ttl_seconds
            if ttl_seconds is not None
            else self.default_ttl
        )

        if ttl <= 0:
            raise ValueError(
                "TTL must be greater than zero."
            )

        entry_id = str(uuid.uuid4())

        try:
            embedding = self._embed(query)

            created_at = time.time()

            metadata = {
                "entry_id": entry_id,
                "query": query,
                "embedding": embedding.tolist(),
                "payload": payload,
                "created_at": created_at,
                "expires_at": created_at + ttl
            }

            metadata_json = json.dumps(metadata)

            vector_values = [
                str(float(value))
                for value in embedding
            ]

            # Add vector to Redis Vector Set.

            self.redis_client.execute_command(
                "VADD",
                self.vector_key,
                "VALUES",
                str(self.dimensions),
                *vector_values,
                entry_id
            )

            try:
                # Store metadata and exact-query mapping atomically.

                with self.redis_client.pipeline(
                    transaction=True
                ) as pipe:

                    pipe.set(
                        self.entry_prefix + entry_id,
                        metadata_json,
                        ex=ttl
                    )

                    pipe.set(
                        self._exact_key(query),
                        metadata_json,
                        ex=ttl
                    )

                    pipe.execute()

            except Exception:
                self.redis_client.execute_command(
                    "VREM",
                    self.vector_key,
                    entry_id
                )

                raise

            self.is_connected = True

        except Exception:
            self.is_connected = False
            raise

    # --------------------------------------------------
    # CACHE STATISTICS
    # --------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:

        try:
            total_entries = sum(
                1
                for _ in self.redis_client.scan_iter(
                    match=self.entry_prefix + "*",
                    count=100
                )
            )

            hits = int(
                self.redis_client.get(
                    self.hits_key
                ) or 0
            )

            misses = int(
                self.redis_client.get(
                    self.misses_key
                ) or 0
            )

            total_lookups = hits + misses

            hit_rate = (
                hits / total_lookups
                if total_lookups
                else 0.0
            )

            self.is_connected = True

            return {
                "total_entries": total_entries,
                "hit_rate": round(hit_rate, 4),
                "redis_connected": True
            }

        except Exception:
            self.is_connected = False

            return {
                "total_entries": 0,
                "hit_rate": 0.0,
                "redis_connected": False
            }
