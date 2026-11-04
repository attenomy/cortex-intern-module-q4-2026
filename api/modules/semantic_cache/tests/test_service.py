
import json
import numpy as np
import pytest

from modules.semantic_cache.service import SemanticCacheService


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.vectors = {}
        self.counters = {}

    def execute_command(self, *args):
        command = str(args[0]).upper()

        if command == "EVAL":
            key = args[3]
            counter = args[4]
            value = self.data.get(key)

            if value:
                self.incr(counter)

            return value

        if command == "VSIM":
            key = args[1]
            vector = np.array(
                [float(v) for v in args[4:4 + int(args[3])]],
                dtype=np.float32
            )

            results = []
            for entry_id, cached in self.vectors.get(key, {}).items():
                score = float(np.dot(vector, cached))
                results.extend([entry_id, str(score)])

            return results

        if command == "VADD":
            key = args[1]
            dimensions = int(args[3])
            vector = np.array(
                [float(v) for v in args[4:4 + dimensions]],
                dtype=np.float32
            )
            entry_id = args[4 + dimensions]
            self.vectors.setdefault(key, {})[entry_id] = vector
            return 1

        if command == "VREM":
            key = args[1]
            for entry_id in args[2:]:
                self.vectors.get(key, {}).pop(entry_id, None)
            return 1

        raise NotImplementedError(command)

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self.data[key] = value
        return True

    def incr(self, key):
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def scan_iter(self, match=None, count=None):
        prefix = match.replace("*", "")
        return iter(
            key for key in self.data
            if key.startswith(prefix)
        )

    def pipeline(self, transaction=False):
        return FakePipeline(self)


class FakePipeline:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.commands = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, key):
        self.commands.append(("get", key))

    def set(self, key, value, ex=None):
        self.commands.append(("set", key, value, ex))

    def execute(self):
        results = []

        for command in self.commands:
            if command[0] == "get":
                results.append(self.redis.get(command[1]))
            else:
                _, key, value, _ttl = command
                self.redis.set(key, value)
                results.append(True)

        return results


@pytest.fixture
def cache():
    service = SemanticCacheService(redis_url="redis://localhost:6379/0")
    service.redis_client = FakeRedis()
    service.dimensions = 3
    return service


def test_normalize_query():
    assert SemanticCacheService._normalize_query(
        "  HELLO   World  "
    ) == "hello world"


def test_exact_cache_key_is_case_insensitive(cache):
    assert cache._exact_key("Hello World") == cache._exact_key(
        "  HELLO   WORLD "
    )


def test_empty_lookup_returns_miss(cache):
    result = cache.lookup("   ")

    assert result["hit"] is False
    assert result["similarity_score"] == 0.0


def test_embedding_rejects_wrong_dimensions(cache, monkeypatch):
    monkeypatch.setattr(
        cache,
        "_get_model",
        lambda: type(
            "Model",
            (),
            {"encode": lambda *args, **kwargs: np.array([1, 2])}
        )()
    )

    with pytest.raises(ValueError):
        cache._embed("hello")


def test_store_rejects_empty_query(cache):
    with pytest.raises(ValueError):
        cache.store("", {"answer": "test"})


def test_store_rejects_empty_payload(cache):
    with pytest.raises(ValueError):
        cache.store("hello", {})


def test_store_rejects_invalid_ttl(cache):
    with pytest.raises(ValueError):
        cache.store("hello", {"answer": "test"}, 0)


def test_exact_lookup_returns_stored_payload(cache):
    metadata = {
        "query": "hello",
        "payload": {"answer": "world"}
    }

    cache.redis_client.data[cache._exact_key("hello")] = json.dumps(
        metadata
    )

    result = cache.lookup("hello")

    assert result["hit"] is True
    assert result["similarity_score"] == 1.0
    assert result["cached_payload"] == {"answer": "world"}


def test_exact_lookup_updates_hit_counter(cache):
    metadata = {"query": "hello", "payload": {"answer": "world"}}

    cache.redis_client.data[cache._exact_key("hello")] = json.dumps(
        metadata
    )

    cache.lookup("hello")

    assert cache.redis_client.counters[cache.hits_key] == 1


def test_redis_failure_returns_cache_miss(cache):
    def fail(*args, **kwargs):
        raise ConnectionError("Redis unavailable")

    cache.redis_client.execute_command = fail

    result = cache.lookup("hello")

    assert result["hit"] is False
    assert result["cached_payload"] is None
    assert cache.is_connected is False


def test_stats_returns_connection_status(cache):
    result = cache.get_stats()

    assert result["redis_connected"] is True
    assert result["total_entries"] == 0
def test_corrupted_metadata_does_not_crash_lookup(cache, monkeypatch):
    cache.redis_client.execute_command = lambda *args: (
        ["broken-entry", "0.99"]
        if str(args[0]).upper() == "VSIM"
        else None
    )

    cache.redis_client.data[
        cache.entry_prefix + "broken-entry"
    ] = "{invalid json"

    monkeypatch.setattr(
        cache,
        "_embed",
        lambda query: np.array([1.0, 0.0, 0.0], dtype=np.float32)
    )

    result = cache.lookup("test query")

    assert result["hit"] is False
    assert result["cached_payload"] is None


def test_expired_vector_is_removed_when_metadata_missing(cache, monkeypatch):
    entry_id = "expired-entry"

    cache.redis_client.vectors[cache.vector_key] = {
        entry_id: np.array([1.0, 0.0, 0.0], dtype=np.float32)
    }

    def fake_execute(*args):
        if str(args[0]).upper() == "EVAL":
            return None
        if str(args[0]).upper() == "VSIM":
            return [entry_id, "0.99"]
        if str(args[0]).upper() == "VREM":
            cache.redis_client.vectors[cache.vector_key].pop(
                entry_id, None
            )
            return 1
        return None

    cache.redis_client.execute_command = fake_execute

    monkeypatch.setattr(
        cache,
        "_embed",
        lambda query: np.array([1.0, 0.0, 0.0], dtype=np.float32)
    )

    result = cache.lookup("test query")

    assert result["hit"] is False
    assert entry_id not in cache.redis_client.vectors[cache.vector_key]
