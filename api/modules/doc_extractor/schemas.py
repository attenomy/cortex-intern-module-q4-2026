from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class DocumentType(str, Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    PURCHASE_ORDER = "purchase_order"


class RegionType(str, Enum):
    HEADER = "header"
    LINE_ITEM_TABLE = "line_item_table"
    TOTALS_BLOCK = "totals_block"


class BoundingBox(BaseModel):
    x_min: float = Field(ge=0)
    y_min: float = Field(ge=0)
    x_max: float = Field(ge=0)
    y_max: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_coordinates(self):
        if self.x_min >= self.x_max:
            raise ValueError("x_min must be less than x_max")

        if self.y_min >= self.y_max:
            raise ValueError("y_min must be less than y_max")

        return self


class LayoutRegion(BaseModel):
    region_type: RegionType
    bounding_box: BoundingBox


class ExtractedEntity(BaseModel):
    value: str | float | None
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: BoundingBox | None = None


class ExtractionRequest(BaseModel):
    document_id: str = Field(
        ...,
        min_length=1,
        description="Unique document identifier"
    )

    document_type: DocumentType

    image_base64: str | None = Field(
        default=None,
        description="Base64-encoded document image"
    )

    raw_content: str | None = Field(
        default=None,
        description="Plain-text document content"
    )

    @model_validator(mode="after")
    def validate_input(self):
        if not self.image_base64 and not self.raw_content:
            raise ValueError(
                "Either image_base64 or raw_content is required"
            )

        if self.image_base64 and self.raw_content:
            raise ValueError(
                "Provide either image_base64 or raw_content, not both"
            )

        return self

DocumentExtractionRequest = ExtractionRequest


class ExtractionResponse(BaseModel):
    document_id: str
    extracted_fields: dict[str, Any]
    schema_valid: bool
    latency_ms: float
