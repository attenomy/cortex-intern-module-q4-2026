import pytest
from modules.doc_extractor.iou_evaluator import calculate_iou, evaluate_regions
from modules.doc_extractor.region_detector import detect_layout_regions
from modules.doc_extractor.schemas import BoundingBox, LayoutRegion, RegionType


def test_iou_partial_overlap():
    a = BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100)
    b = BoundingBox(x_min=50, y_min=50, x_max=150, y_max=150)
    assert calculate_iou(a, b) == pytest.approx(1 / 7)
def test_iou_no_overlap():
    a = BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10)
    b = BoundingBox(x_min=20, y_min=20, x_max=30, y_max=30)
    assert calculate_iou(a, b) == 0.0
def test_iou_invalid_box():
    a = {"x_min": 10, "y_min": 10, "x_max": 0, "y_max": 20}
    b = {"x_min": 0, "y_min": 0, "x_max": 10, "y_max": 10}
    with pytest.raises(ValueError):
        calculate_iou(a, b)
def test_missing_prediction_scores_zero():
    gt = [
        LayoutRegion(
            region_type=RegionType.HEADER,
            bounding_box=BoundingBox(
                x_min=0, y_min=0, x_max=100, y_max=50
            ),
        )
    ]
    result = evaluate_regions([], gt)
    assert result["regions"]["header"] == 0.0
    assert result["target_met"] is False
def test_invalid_image_dimensions():
    with pytest.raises(ValueError):
        detect_layout_regions([], 0, 100)
def test_empty_words():
    assert detect_layout_regions([], 100, 100) == []
from unittest.mock import patch

from modules.doc_extractor.service import DocumentExtractor


def test_image_extraction_returns_detected_regions():
    fake_words = [
        {"text": "ABC STORE", "confidence": 0.95,
         "bounding_box": {"x_min": 20, "y_min": 20, "x_max": 120, "y_max": 45}},
        {"text": "QTY", "confidence": 0.95,
         "bounding_box": {"x_min": 20, "y_min": 300, "x_max": 60, "y_max": 320}},
        {"text": "PRICE", "confidence": 0.95,
         "bounding_box": {"x_min": 100, "y_min": 300, "x_max": 150, "y_max": 320}},
        {"text": "AMOUNT", "confidence": 0.95,
         "bounding_box": {"x_min": 200, "y_min": 300, "x_max": 270, "y_max": 320}},
        {"text": "TOTAL", "confidence": 0.95,
         "bounding_box": {"x_min": 200, "y_min": 600, "x_max": 270, "y_max": 625}},
        {"text": "CASH", "confidence": 0.95,
         "bounding_box": {"x_min": 200, "y_min": 650, "x_max": 250, "y_max": 675}},
    ]
    extractor = DocumentExtractor()
    fake_image = type(
        "FakeImage",
        (),
        {"width": 463, "height": 1013, "convert": lambda self, mode: self},
    )()
    with (
        patch("modules.doc_extractor.service.decode_document_image", return_value=fake_image),
        patch.object(
            extractor.ocr,
            "extract_text_with_confidence",
            return_value={"text": "ABC STORE QTY PRICE AMOUNT TOTAL CASH", "words": fake_words},
        ),
    ):
        result = extractor.extract_document(
            doc_id="integration-001",
            doc_type="receipt",
            raw_content="fake-base64",
            is_image=True,
        )
    regions = result["extracted_fields"]["detected_regions"]
    names = {region["region_type"] for region in regions}
    assert names == {"header", "line_item_table", "totals_block"}
    assert result["document_id"] == "integration-001"

def test_single_code_anchor_detects_table():
    words = [
        {"text": "STORE", "bounding_box": {"x_min": 10, "y_min": 20, "x_max": 60, "y_max": 40}},
        {"text": "CODE", "bounding_box": {"x_min": 10, "y_min": 300, "x_max": 60, "y_max": 320}},
        {"text": "123", "bounding_box": {"x_min": 10, "y_min": 350, "x_max": 40, "y_max": 370}},
        {"text": "TOTAL", "bounding_box": {"x_min": 10, "y_min": 600, "x_max": 60, "y_max": 620}},
    ]
    regions = detect_layout_regions(words, 500, 800)
    names = {r.region_type.value for r in regions}
    assert "line_item_table" in names
    assert "header" in names
def test_table_fallback_without_column_headers():
    words = [
        {"text": "STORE", "bounding_box": {"x_min": 10, "y_min": 20, "x_max": 60, "y_max": 40}},
        {"text": "Apple", "bounding_box": {"x_min": 10, "y_min": 300, "x_max": 80, "y_max": 320}},
        {"text": "120", "bounding_box": {"x_min": 200, "y_min": 300, "x_max": 240, "y_max": 320}},
        {"text": "Bread", "bounding_box": {"x_min": 10, "y_min": 340, "x_max": 80, "y_max": 360}},
        {"text": "80", "bounding_box": {"x_min": 200, "y_min": 340, "x_max": 230, "y_max": 360}},
        {"text": "TOTAL", "bounding_box": {"x_min": 10, "y_min": 600, "x_max": 60, "y_max": 620}},
    ]
    regions = detect_layout_regions(words, 500, 800)
    names = {r.region_type.value for r in regions}
    assert "line_item_table" in names
