from decimal import Decimal, InvalidOperation
from typing import Any


def _parse_amount(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    text = text.replace(",", "").replace("RM", "").replace("$", "")
    text = text.replace("₹", "").replace("€", "").replace("£", "").strip()
    try:
        amount = Decimal(text)
        if not amount.is_finite():
            return None
        return float(amount)
    except (InvalidOperation, ValueError):
        return None
def adapt_sroie_entities(record: dict[str, Any]) -> dict[str, Any]:
    """Convert SROIE annotations without inventing missing invoice fields."""
    if not isinstance(record, dict):
        raise TypeError("SROIE record must be a dictionary")
    source = record.get("entities", {})
    if not isinstance(source, dict):
        raise ValueError("SROIE entities must be a dictionary")
    def first_value(key: str) -> str | None:
        value = source.get(key)
        if isinstance(value, list):
            value = value[0] if value else None
        if value is None:
            return None
        value = str(value).strip()
        return value or None
    return {
        "vendor_name": first_value("vendor_name"),
        "invoice_number": None,
        "net_amount": _parse_amount(first_value("total")),
        "currency": None,
        "date": first_value("date"),
        "address": first_value("address"),
        "source": "SROIE",
        "document_id": record.get("document_id"),
    }
