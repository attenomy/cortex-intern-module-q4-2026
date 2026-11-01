import pytest

def test_router_finance_intent(client):
    payload = {
        "query": "Find invoice total for Q3 vendor AWS",
        "client_tier": "Enterprise"
    }
    response = client.post("/api/v1/router", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent_category"] == "finance"
    assert data["target_pipeline"] == "invoice_extraction_pipeline"
    assert data["confidence"] > 0.60
    assert data["latency_ms"] > 0.0

def test_router_support_intent(client):
    payload = {
        "query": "Encountered a critical bug and login broken error in dashboard",
        "client_tier": "Pro"
    }
    response = client.post("/api/v1/router", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent_category"] == "support"
    assert data["target_pipeline"] == "agent_triage_pipeline"

def test_router_search_intent_fallback(client):
    payload = {
        "query": "How to find architectural system documentation",
        "client_tier": "Starter"
    }
    response = client.post("/api/v1/router", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent_category"] == "search"
    assert data["target_pipeline"] == "semantic_knowledge_rag"

def test_router_empty_query_rejected(client):
    payload = {
        "query": "",
        "client_tier": "Enterprise"
    }
    response = client.post("/api/v1/router", json=payload)
    assert response.status_code == 400
    assert "Query string cannot be empty" in response.json()["detail"]

def test_router_whitespace_only_query_rejected(client):
    payload = {
        "query": "    \t\n   ",
        "client_tier": "Enterprise"
    }
    response = client.post("/api/v1/router", json=payload)
    assert response.status_code == 400
    assert "Query string cannot be empty" in response.json()["detail"]

def test_router_missing_payload_field_422(client):
    payload = {
        "client_tier": "Enterprise"
    }
    response = client.post("/api/v1/router", json=payload)
    assert response.status_code == 422

