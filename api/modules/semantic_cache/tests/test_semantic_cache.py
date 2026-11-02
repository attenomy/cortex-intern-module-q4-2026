from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cache_miss_initially():
    payload = {"query": "unique new query 12345"}
    res = client.post("/api/v1/cache/lookup", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["hit"] is False
    assert data["latency_ms"] < 10.0

def test_cache_empty_query_400():
    res = client.post("/api/v1/cache/lookup", json={"query": ""})
    assert res.status_code == 400

def test_cache_stats():
    res = client.get("/api/v1/cache/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_entries" in data
    assert "hit_rate" in data

