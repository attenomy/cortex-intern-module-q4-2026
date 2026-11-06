import pytest
from modules.doc_extractor.schemas import (
    BoundingBox,
    LayoutRegion,
    RegionType,
)
from pydantic import ValidationError


def test_valid_bounding_box():
    box = BoundingBox(
        x_min=10,
        y_min=20,
        x_max=200,
        y_max=150
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
            y_max=150
        )


def test_bounding_box_rejects_invalid_x_coordinates():
    with pytest.raises(ValidationError):
        BoundingBox(
            x_min=200,
            y_min=20,
            x_max=100,
            y_max=150
        )


def test_bounding_box_rejects_invalid_y_coordinates():
    with pytest.raises(ValidationError):
        BoundingBox(
            x_min=10,
            y_min=150,
            x_max=200,
            y_max=100
        )


def test_layout_region_valid():
    box = BoundingBox(
        x_min=10,
        y_min=20,
        x_max=200,
        y_max=150
    )

    region = LayoutRegion(
        region_type=RegionType.HEADER,
        bounding_box=box
    )

    assert region.region_type == RegionType.HEADER
    assert region.bounding_box.x_max == 200
