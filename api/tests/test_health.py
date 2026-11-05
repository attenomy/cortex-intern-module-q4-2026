def test_health_check_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "attenomy-cortex-engine"
    assert data["version"] == "1.0.0"
    assert "model_loaded" in data
    assert data["uptime_seconds"] >= 0.0

