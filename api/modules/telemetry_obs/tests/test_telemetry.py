
from fastapi import FastAPI
from fastapi.testclient import TestClient
from modules.telemetry_obs.middleware import TelemetryMiddleware
from modules.telemetry_obs.router import router as telemetry_router

app = FastAPI()

app.include_router(telemetry_router)
app.add_middleware(TelemetryMiddleware)

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "attenomy-cortex-engine"
    assert data["version"] == "1.0.0"
    assert "uptime_seconds" in data


def test_metrics_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "cortex_uptime_seconds" in response.text
    assert "cortex_requests_total" in response.text
    assert "cortex_request_latency_seconds" in response.text
    assert "cortex_cache_hits_total" in response.text
    assert "cortex_active_workers" in response.text


def test_latency_histogram_buckets():
    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200

    metrics = response.text

    expected_buckets = [
        'le="0.005"',
        'le="0.01"',
        'le="0.025"',
        'le="0.05"',
        'le="0.1"',
        'le="0.25"',
        'le="0.5"',
        'le="1.0"',
        'le="+Inf"',
    ]

    for bucket in expected_buckets:
        assert bucket in metrics
