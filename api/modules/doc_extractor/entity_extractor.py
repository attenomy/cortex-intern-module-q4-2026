import re
from decimal import Decimal, InvalidOperation
from typing import Any


def extract_invoice_entities(ocr_text: str) -> dict[str, Any]:
    """Extract basic invoice entities using OCR text."""

    text = ocr_text.strip()

    if not text:
        return {
            "vendor_name": None,
            "invoice_number": None,
            "net_amount": None,
            "currency": None,
        }

    # Extract invoice number
    invoice_match = re.search(
        r"(?:inv(?:oice)?\s*(?:no\.?|number|#)\s*[:.]?\s*)"
        r"([A-Z0-9][A-Z0-9/-]*)",
        text,
        re.IGNORECASE,
    )

    invoice_number = (
        invoice_match.group(1).strip()
        if invoice_match else None
    )

    # Detect currency
    currency_patterns = {
        "INR": r"\bINR\b|₹",
        "USD": r"\bUSD\b|\$",
        "EUR": r"\bEUR\b|€",
        "GBP": r"\bGBP\b|£",
    }

    currency = None

    for code, pattern in currency_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            currency = code
            break

    # Extract net amount
    amount_match = re.search(
        r"(?:net\s*amount|grand\s*total|total\s*amount|total|for)"
        r"\s*[:\-]?\s*(?:INR|USD|EUR|GBP|₹|\$|€|£)?\s*"
        r"([\d,]+(?:\.\d{1,2})?)",
        text,
        re.IGNORECASE,
    )

    net_amount = None

    if amount_match:
        try:
            amount = float(amount_match.group(1).replace(",", ""))
            if amount > 0:
                net_amount = amount
        except ValueError:
            pass

    # Extract vendor name
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    vendor_name = None

    vendor_match = re.search(
        r"\bfrom\s+(.+?)\s+for\b",
        text,
        re.IGNORECASE,
    )
    if vendor_match:
        vendor_name = vendor_match.group(1).strip()
    else:
        heading_match = re.search(
            r"^([A-Z][A-Z0-9&.,' -]+?)\s+(?:COMMERCIAL\s+)?INVOICE\b",
            text,
            re.IGNORECASE,
        )
        if heading_match:
            vendor_name = heading_match.group(1).strip()
        elif lines:
            first_line = lines[0]
            if not re.search(
                r"invoice|receipt|purchase order|tax invoice",
                first_line,
                re.IGNORECASE,
            ):
                vendor_name = first_line
    return {
        "vendor_name": vendor_name,
        "invoice_number": invoice_number,
        "net_amount": net_amount,
        "currency": currency,
    }


def _normalize(value: str) -> str:
    """Normalize text and equivalent numeric values."""

    value = value.strip()

    try:
        number = Decimal(value.replace(",", ""))
        return format(number.normalize(), "f")
    except InvalidOperation:
        return re.sub(r"[^a-z0-9]", "", value.lower())


def _calculate_confidence(
    value: Any,
    ocr_words: list[dict[str, Any]],
) -> float | None:

    if value is None:
        return None

    target = _normalize(str(value))

    if not target:
        return None

    normalized_words = []

    for word in ocr_words:
        word_text = str(word.get("text", "")).strip()

        try:
            confidence = float(word["confidence"])
        except (KeyError, TypeError, ValueError):
            continue

        if not word_text or not 0 <= confidence <= 1:
            continue

        normalized = _normalize(word_text)

        if normalized:
            normalized_words.append((normalized, confidence))

    for start in range(len(normalized_words)):
        combined = ""

        for end in range(start, len(normalized_words)):
            combined += normalized_words[end][0]

            if combined == target:
                scores = [
                    item[1]
                    for item in normalized_words[start:end + 1]
                ]

                return round(sum(scores) / len(scores), 4)

            if len(combined) >= len(target):
                break

    return None


def extract_invoice_entities_with_confidence(
    ocr_data: dict[str, Any],
) -> dict[str, Any]:

    ocr_text = ocr_data.get("text", "")
    ocr_words = ocr_data.get("words", [])

    entities = extract_invoice_entities(ocr_text)

    confidence = {
        field: _calculate_confidence(value, ocr_words)
        for field, value in entities.items()
    }

    return {
        "entities": entities,
        "confidence": confidence,
    }
