from typing import Any

import pycountry
from pydantic import BaseModel, ValidationError, field_validator, model_validator


class InvoiceEntities(BaseModel):
    vendor_name: str | None = None
    invoice_number: str | None = None
    net_amount: float | None = None
    currency: str | None = None

    @field_validator("vendor_name", "invoice_number")
    @classmethod
    def validate_text_fields(cls, value):
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Field cannot be empty")
        return value

    @field_validator("net_amount")
    @classmethod
    def validate_amount(cls, value):
        if value is not None and value <= 0:
            raise ValueError("Net amount must be greater than zero")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value):
        if value is None:
            return value

        value = value.upper()

        if not pycountry.currencies.get(alpha_3=value):
            raise ValueError("Invalid ISO-4217 currency code")

        return value

    @model_validator(mode="after")
    def validate_required_fields(self):
        required = [
            "vendor_name",
            "invoice_number",
            "net_amount",
            "currency"
        ]

        missing = [
            field for field in required
            if getattr(self, field) is None
        ]

        if missing:
            raise ValueError(
                f"Missing mandatory invoice fields: {', '.join(missing)}"
            )

        return self


def validate_invoice_entities(
    entities: dict[str, Any]
) -> tuple[bool, dict[str, Any], list[str]]:

    try:
        validated = InvoiceEntities.model_validate(entities)

        return True, validated.model_dump(), []

    except ValidationError as exc:
        errors = [
            error["msg"]
            for error in exc.errors()
        ]

        return False, entities, errors
