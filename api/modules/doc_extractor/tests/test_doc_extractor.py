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
from modules.doc_extractor.service import DocumentExtractor
def test_service_extracts_valid_plain_text_invoice():
    extractor = DocumentExtractor()
    result = extractor.extract_document(
        doc_id="text-invoice-001",
        doc_type="invoice",
        raw_content=(
            "ABC STORE\n"
            "Invoice No: INV-123\n"
            "Currency: USD\n"
            "Net Amount: USD 120.00"
        ),
        is_image=False,
    )
    assert result["document_id"] == "text-invoice-001"
    assert result["schema_valid"] is True
    assert result["extracted_fields"]["extracted_entities"]["invoice_number"] == "INV-123"
def test_service_rejects_empty_invoice_text():
    extractor = DocumentExtractor()
    result = extractor.extract_document(
        doc_id="empty-invoice-001",
        doc_type="invoice",
        raw_content="",
        is_image=False,
    )
    assert result["schema_valid"] is False
    assert result["extracted_fields"]["validation_errors"]
def test_service_handles_unsupported_document_type():
    extractor = DocumentExtractor()
    result = extractor.extract_document(
        doc_id="contract-001",
        doc_type="contract",
        raw_content="Sample contract text",
        is_image=False,
    )
    assert result["schema_valid"] is False
    assert result["extracted_fields"]["validation_errors"] == [
        "Entity extraction is not implemented for contract"
    ]

def test_classifier_prediction_and_confidence_are_returned():
    extractor = DocumentExtractor()
    extractor.set_classifier(object())
    image = base64.b64decode(create_test_image_base64())
    mock_ocr = {
        "text": "Invoice No: INV-123",
        "words": [{"text": "Invoice", "confidence": 0.98}],
    }
    with patch(
        "modules.doc_extractor.service.predict_document",
        return_value={"document_type": "invoice", "confidence": 0.94},
    ), patch.object(
        extractor.ocr,
        "extract_text_with_confidence",
        return_value=mock_ocr,
    ):
        result = extractor.extract_document(
            "classified-invoice-001",
            "invoice",
            base64.b64encode(image).decode("utf-8"),
            is_image=True,
        )
    fields = result["extracted_fields"]
    assert fields["requested_doc_type"] == "invoice"
    assert fields["predicted_doc_type"] == "invoice"
    assert fields["classification_confidence"] == 0.94
    assert fields["validation_warnings"] == []
def test_classifier_mismatch_generates_validation_warning():
    extractor = DocumentExtractor()
    extractor.set_classifier(object())
    image = base64.b64decode(create_test_image_base64())
    mock_ocr = {
        "text": "Sample receipt",
        "words": [{"text": "Receipt", "confidence": 0.96}],
    }
    with patch(
        "modules.doc_extractor.service.predict_document",
        return_value={"document_type": "receipt", "confidence": 0.87},
    ), patch.object(
        extractor.ocr,
        "extract_text_with_confidence",
        return_value=mock_ocr,
    ):
        result = extractor.extract_document(
            "mismatch-001",
            "invoice",
            base64.b64encode(image).decode("utf-8"),
            is_image=True,
        )
    fields = result["extracted_fields"]
    assert fields["requested_doc_type"] == "invoice"
    assert fields["predicted_doc_type"] == "receipt"
    assert fields["doc_type"] == "receipt"
    assert fields["classification_confidence"] == 0.87
    assert len(fields["validation_warnings"]) == 1
    assert "does not match classifier prediction" in (
        fields["validation_warnings"][0]
    )
def test_plain_text_extraction_has_no_classifier_metadata():
    extractor = DocumentExtractor()
    result = extractor.extract_document(
        "plain-text-002",
        "invoice",
        "ABC STORE\nInvoice No: INV-123\nCurrency: USD\nNet Amount: USD 120.00",
        is_image=False,
    )
    fields = result["extracted_fields"]
    assert fields["requested_doc_type"] == "invoice"
    assert fields["predicted_doc_type"] is None
    assert fields["classification_confidence"] is None
    assert fields["validation_warnings"] == []
