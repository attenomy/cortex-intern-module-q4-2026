import pytest

def test_extract_valid_invoice_payload(client):
    payload = {
        "document_id": "doc_inv_1049",
        "document_type": "invoice",
        "raw_content": "Invoice # INV-2026-9021 from Attenomy Systems for $4,500.00"
    }
    response = client.post("/api/v1/extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc_inv_1049"
    assert data["schema_valid"] is True
    assert "extracted_fields" in data
    assert data["latency_ms"] > 0.0

def test_extract_missing_document_id_422(client):
    payload = {
        "document_type": "invoice",
        "raw_content": "Some text"
    }
    response = client.post("/api/v1/extract", json=payload)
    assert response.status_code == 422

def test_extract_missing_document_type_422(client):
    payload = {
        "document_id": "doc_inv_1050",
        "raw_content": "Some text"
    }
    response = client.post("/api/v1/extract", json=payload)
    assert response.status_code == 422

