import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_intent_router_finance():
    res = client.post("/api/v1/router", json={"query": "Find invoice total for Q3 AWS"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent_category"] == "finance"
    assert data["target_pipeline"] == "invoice_extraction_pipeline"
    assert data["confidence"] > 0.60
    assert data["latency_ms"] > 0.0

def test_intent_router_support():
    res = client.post("/api/v1/router", json={"query": "Found an issue and login crash error"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent_category"] == "support"
    assert data["target_pipeline"] == "agent_triage_pipeline"

def test_intent_router_search_fallback():
    res = client.post("/api/v1/router", json={"query": "Explain system architecture"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent_category"] == "search"
    assert data["target_pipeline"] == "semantic_knowledge_rag"

def test_intent_router_empty_query_400():
    res = client.post("/api/v1/router", json={"query": ""})
    assert res.status_code == 400
    assert "Query string cannot be empty" in res.json()["detail"]

def test_intent_router_whitespace_400():
    res = client.post("/api/v1/router", json={"query": "   \n\t  "})
    assert res.status_code == 400
