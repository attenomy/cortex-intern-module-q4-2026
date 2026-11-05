
import pytest
from fastapi.testclient import TestClient

from main import app
from modules.semantic_cache.router import service


client = TestClient(app)


# ==========================================
# LOOKUP TESTS
# ==========================================

def test_cache_lookup_miss(monkeypatch):
    monkeypatch.setattr(
        service,
        "lookup",
        lambda query, threshold: {
            "hit": False,
            "matched_query": None,
            "similarity_score": 0.0,
            "cached_payload": None,
            "latency_ms": 1.0,
            "embedding_latency_ms": 0.0,
            "redis_latency_ms": 1.0,
            "timings": {}
        }
    )

    response = client.post(
        "/api/v1/cache/lookup",
        json={"query": "unique test query"}
    )

    assert response.status_code == 200
    assert response.json()["hit"] is False


def test_cache_lookup_passes_query_and_threshold(monkeypatch):
    captured = {}

    def fake_lookup(query, threshold):
        captured["query"] = query
        captured["threshold"] = threshold

        return {
            "hit": False,
            "matched_query": None,
            "similarity_score": 0.0,
            "cached_payload": None,
            "latency_ms": 1.0,
            "embedding_latency_ms": 0.0,
            "redis_latency_ms": 1.0
        }

    monkeypatch.setattr(service, "lookup", fake_lookup)

    response = client.post(
        "/api/v1/cache/lookup",
        json={
            "query": "Python programming",
            "threshold": 0.90
        }
    )

    assert response.status_code == 200
    assert captured["query"] == "Python programming"
    assert captured["threshold"] == 0.90


def test_cache_empty_query_400():
    response = client.post(
        "/api/v1/cache/lookup",
        json={"query": ""}
    )

    assert response.status_code == 400


def test_cache_missing_query_422():
    response = client.post(
        "/api/v1/cache/lookup",
        json={}
    )

    assert response.status_code == 422


def test_cache_threshold_below_minimum_422():
    response = client.post(
        "/api/v1/cache/lookup",
        json={
            "query": "Python",
            "threshold": 0.49
        }
    )

    assert response.status_code == 422


def test_cache_threshold_above_maximum_422():
    response = client.post(
        "/api/v1/cache/lookup",
        json={
            "query": "Python",
            "threshold": 1.01
        }
    )

    assert response.status_code == 422


def test_cache_lookup_rejects_extra_fields_422():
    response = client.post(
        "/api/v1/cache/lookup",
        json={
            "query": "Python",
            "unknown": "invalid"
        }
    )

    assert response.status_code == 422


# ==========================================
# STORE TESTS
# ==========================================

def test_cache_store_success(monkeypatch):
    monkeypatch.setattr(
        service,
        "store",
        lambda query, payload, ttl_seconds: True
    )

    response = client.post(
        "/api/v1/cache/store",
        json={
            "query": "What is Python?",
            "payload": {
                "answer": "Python is a programming language."
            }
        }
    )

    assert response.status_code == 200
    assert response.json()["stored"] is True


def test_cache_store_passes_ttl(monkeypatch):
    captured = {}

    def fake_store(query, payload, ttl_seconds):
        captured["ttl"] = ttl_seconds

    monkeypatch.setattr(service, "store", fake_store)

    response = client.post(
        "/api/v1/cache/store",
        json={
            "query": "TTL test",
            "payload": {"answer": "Test"},
            "ttl_seconds": 120
        }
    )

    assert response.status_code == 200
    assert captured["ttl"] == 120


def test_cache_store_empty_query_400(monkeypatch):
    monkeypatch.setattr(
        service,
        "store",
        lambda **kwargs: None
    )

    response = client.post(
        "/api/v1/cache/store",
        json={
            "query": "",
            "payload": {"answer": "Test"}
        }
    )

    assert response.status_code == 400


def test_cache_store_missing_payload_422():
    response = client.post(
        "/api/v1/cache/store",
        json={"query": "Python"}
    )

    assert response.status_code == 422


def test_cache_store_empty_payload_422():
    response = client.post(
        "/api/v1/cache/store",
        json={
            "query": "Python",
            "payload": {}
        }
    )

    assert response.status_code == 422


def test_cache_store_zero_ttl_422():
    response = client.post(
        "/api/v1/cache/store",
        json={
            "query": "Python",
            "payload": {"answer": "Test"},
            "ttl_seconds": 0
        }
    )

    assert response.status_code == 422


def test_cache_store_negative_ttl_422():
    response = client.post(
        "/api/v1/cache/store",
        json={
            "query": "Python",
            "payload": {"answer": "Test"},
            "ttl_seconds": -10
        }
    )

    assert response.status_code == 422


def test_cache_store_rejects_extra_fields_422():
    response = client.post(
        "/api/v1/cache/store",
        json={
            "query": "Python",
            "payload": {"answer": "Test"},
            "unknown": "invalid"
        }
    )

    assert response.status_code == 422


# ==========================================
# STATS TEST
# ==========================================

def test_cache_stats(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_stats",
        lambda: {
            "total_entries": 5,
            "hit_rate": 0.75,
            "redis_connected": True
        }
    )

    response = client.get("/api/v1/cache/stats")

    assert response.status_code == 200

    data = response.json()

    assert data["total_entries"] == 5
    assert data["hit_rate"] == 0.75
    assert data["redis_connected"] is True
