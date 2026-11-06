import base64
import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app
from modules.doc_extractor.router import service
from PIL import Image

client = TestClient(app)


def create_test_image_base64():
    image = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def test_extract_invoice_valid():
    payload = {
        "document_id": "doc_inv_101",
        "document_type": "invoice",
        "image_base64": create_test_image_base64()
    }

    mock_ocr_data = {
        "text": "Invoice # INV-2026-9021 for $4,500.00",
        "words": [
            {"text": "Invoice", "confidence": 0.98},
            {"text": "#", "confidence": 0.95},
            {"text": "INV-2026-9021", "confidence": 0.97},
            {"text": "for", "confidence": 0.96},
            {"text": "$", "confidence": 0.95},
            {"text": "4,500.00", "confidence": 0.99}
        ]
    }

    with patch.object(
        service.ocr,
        "extract_text_with_confidence",
        return_value=mock_ocr_data
    ):
        res = client.post("/api/v1/extract", json=payload)

    assert res.status_code == 200

    data = res.json()

    assert data["document_id"] == "doc_inv_101"

    assert data["extracted_fields"]["ocr_text"] == (
        "Invoice # INV-2026-9021 for $4,500.00"
    )

    assert "entity_confidence" in data["extracted_fields"]


def test_extract_empty_id_400():
    payload = {
        "document_id": "   ",
        "document_type": "invoice",
        "image_base64": create_test_image_base64()
    }

    res = client.post("/api/v1/extract", json=payload)

    assert res.status_code == 400


def test_extract_missing_type_422():
    payload = {
        "document_id": "doc_inv_102",
        "image_base64": create_test_image_base64()
    }

    res = client.post("/api/v1/extract", json=payload)

    assert res.status_code == 422

def test_extract_invalid_base64():
    payload = {
        "document_id": "doc_invalid_101",
        "document_type": "invoice",
        "image_base64": "this_is_not_valid_base64"
    }

    response = client.post("/api/v1/extract", json=payload)

    assert response.status_code == 422
