import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_extract_invoice_valid():
    payload = {
        "document_id": "doc_inv_101",
        "document_type": "invoice",
        "raw_content": "Invoice # INV-2026-9021 for $4,500.00"
    }
    res = client.post("/api/v1/extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["document_id"] == "doc_inv_101"
    assert data["schema_valid"] is True
    assert "extracted_fields" in data

def test_extract_empty_id_400():
    payload = {
        "document_id": "   ",
        "document_type": "invoice",
        "raw_content": "Invoice data"
    }
    res = client.post("/api/v1/extract", json=payload)
    assert res.status_code == 400
    assert "document_id cannot be empty" in res.json()["detail"]

def test_extract_missing_type_422():
    payload = {
        "document_id": "doc_inv_102",
        "raw_content": "Invoice data"
    }
    res = client.post("/api/v1/extract", json=payload)
    assert res.status_code == 422

