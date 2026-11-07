import pytest
from modules.doc_extractor.schemas import (
    BoundingBox,
    ExtractedEntity,
    ExtractionRequest,
    LayoutRegion,
    RegionType,
)
from pydantic import ValidationError


def test_valid_bounding_box():
    box = BoundingBox(
        x_min=10,
        y_min=20,
        x_max=200,
        y_max=150,
    )

    assert box.x_min == 10
    assert box.y_min == 20
    assert box.x_max == 200
    assert box.y_max == 150


def test_bounding_box_rejects_negative_coordinates():
    with pytest.raises(ValidationError):
        BoundingBox(
            x_min=-10,
            y_min=20,
            x_max=200,
            y_max=150,
        )


def test_bounding_box_rejects_invalid_x_coordinates():
    with pytest.raises(ValidationError):
        BoundingBox(
            x_min=200,
            y_min=20,
            x_max=100,
            y_max=150,
        )


def test_bounding_box_rejects_invalid_y_coordinates():
    with pytest.raises(ValidationError):
        BoundingBox(
            x_min=10,
            y_min=150,
            x_max=200,
            y_max=100,
        )


def test_layout_region_valid():
    box = BoundingBox(
        x_min=10,
        y_min=20,
        x_max=200,
        y_max=150,
    )

    region = LayoutRegion(
        region_type=RegionType.HEADER,
        bounding_box=box,
    )

    assert region.region_type == RegionType.HEADER
    assert region.bounding_box.x_max == 200


def test_confidence_rejects_value_below_zero():
    with pytest.raises(ValidationError):
        ExtractedEntity(value="Invoice", confidence=-0.1)


def test_confidence_rejects_value_above_one():
    with pytest.raises(ValidationError):
        ExtractedEntity(value="Invoice", confidence=1.1)


def test_extraction_request_rejects_missing_content():
    with pytest.raises(ValidationError):
        ExtractionRequest(
            document_id="doc-101",
            document_type="invoice",
        )


def test_extraction_request_rejects_both_content_fields():
    with pytest.raises(ValidationError):
        ExtractionRequest(
            document_id="doc-102",
            document_type="invoice",
            image_base64="encoded-image",
            raw_content="Invoice text",
        )


def test_extraction_request_rejects_empty_document_id():
    with pytest.raises(ValidationError):
        ExtractionRequest(
            document_id="",
            document_type="invoice",
            raw_content="Invoice text",
        )

def test_bounding_box_rejects_equal_x_coordinates():
    with pytest.raises(ValidationError):
        BoundingBox(x_min=10, y_min=10, x_max=10, y_max=100)


def test_bounding_box_rejects_equal_y_coordinates():
    with pytest.raises(ValidationError):
        BoundingBox(x_min=10, y_min=20, x_max=100, y_max=20)


def test_bounding_box_rejects_negative_y_coordinate():
    with pytest.raises(ValidationError):
        BoundingBox(x_min=10, y_min=-5, x_max=100, y_max=100)


def test_bounding_box_rejects_negative_max_coordinate():
    with pytest.raises(ValidationError):
        BoundingBox(x_min=10, y_min=10, x_max=-1, y_max=100)


def test_extraction_request_rejects_invalid_document_type():
    with pytest.raises(ValidationError):
        ExtractionRequest(
            document_id="doc-103",
            document_type="unknown",
            raw_content="Invoice text",
        )


def test_extraction_request_rejects_missing_document_id():
    with pytest.raises(ValidationError):
        ExtractionRequest(
            document_type="invoice",
            raw_content="Invoice text",
        )


def test_extracted_entity_rejects_non_numeric_confidence():
    with pytest.raises(ValidationError):
        ExtractedEntity(value="Invoice", confidence="invalid")


def test_extracted_entity_rejects_missing_confidence():
    with pytest.raises(ValidationError):
        ExtractedEntity(value="Invoice")


def test_layout_region_rejects_invalid_region_type():
    with pytest.raises(ValidationError):
        LayoutRegion(
            region_type="unknown",
            bounding_box=BoundingBox(
                x_min=0, y_min=0, x_max=100, y_max=100
            ),
        )
