import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "attenomy-cortex-engine"
    assert data["version"] == "1.0.0"

def test_metrics_endpoint():
    res = client.get("/metrics")
    assert res.status_code == 200
    text = res.text
    assert "cortex_uptime_seconds" in text
    assert "cortex_requests_total" in text
