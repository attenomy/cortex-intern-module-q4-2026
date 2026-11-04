
import hashlib
import json
import os
import time
import uuid
import threading
from typing import Any, Dict, Optional

import numpy as np
import redis


class SemanticCacheService:
    """Redis-backed semantic cache with performance instrumentation."""

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

        self.vector_key = "semantic_cache:vectors"
        self.entry_prefix = "semantic_cache:entry:"
        self.exact_prefix = "semantic_cache:exact:"
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

    def _exact_key(self, query: str) -> str:
        normalized = self._normalize_query(query)

        query_hash = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        return self.exact_prefix + query_hash

    # --------------------------------------------------
    # EMBEDDING MODEL
    # --------------------------------------------------

    def _get_model(self):
        """Load the embedding model only when required."""

        if self._model is None:
            with self._model_lock:
                if self._model is None:

                    # Lazy import: avoids loading ML dependencies
                    # when the service only needs Redis.
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
                    # Remove stale or corrupted vector entries.
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

            # Calculate Redis operation latency.

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
            # Generate embedding.

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
                # Roll back vector if metadata storage fails.

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
