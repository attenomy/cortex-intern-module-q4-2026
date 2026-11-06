import time
from typing import Any

import pytesseract
from fastapi import HTTPException

from .image_utils import decode_document_image
from .entity_extractor import (
    extract_invoice_entities,
    extract_invoice_entities_with_confidence,
)
from .entity_validator import validate_invoice_entities
from .ocr import OCRProvider, TesseractOCR


class DocumentExtractor:
    """Cognitive document extraction pipeline."""

    def __init__(self, ocr_provider: OCRProvider | None = None):
        self.ocr = ocr_provider or TesseractOCR()
        self.is_ready = True

    def extract_document(
        self,
        doc_id: str,
        doc_type: str,
        raw_content: str,
        is_image: bool = True,
    ) -> dict[str, Any]:

        start_time = time.perf_counter()

        try:
            # Step 1: Extract document text
            if is_image:
                image = decode_document_image(raw_content)

                ocr_data = self.ocr.extract_text_with_confidence(image)

                extracted_text = ocr_data.get("text", "")
                ocr_words = ocr_data.get("words", [])

            else:
                extracted_text = raw_content.strip()

                ocr_data = {
                    "text": extracted_text,
                    "words": [],
                }

                ocr_words = []

            # Step 2: Extract entities
            if doc_type == "invoice":

                if is_image:
                    result = extract_invoice_entities_with_confidence(
                        ocr_data
                    )

                    entities = result["entities"]
                    entity_confidence = result["confidence"]

                else:
                    entities = extract_invoice_entities(extracted_text)

                    # Plain text has no OCR confidence scores.
                    entity_confidence = {
                        field: None
                        for field in entities
                    }

                # Step 3: Validate extracted entities
                (
                    schema_valid,
                    entities,
                    validation_errors,
                ) = validate_invoice_entities(entities)

            else:
                # Other document classes are not yet implemented.
                entities = {}
                entity_confidence = {}
                schema_valid = False
                validation_errors = [
                    f"Entity extraction is not implemented for {doc_type}"
                ]

        except HTTPException:
            raise

        except pytesseract.TesseractNotFoundError:
            raise HTTPException(
                status_code=503,
                detail="Tesseract OCR engine is unavailable",
            )

        except pytesseract.TesseractError:
            raise HTTPException(
                status_code=500,
                detail="OCR processing failed",
            )

        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        # Step 4: Build response
        return {
            "document_id": doc_id,
            "extracted_fields": {
                "doc_type": doc_type,
                "ocr_text": extracted_text,
                "extracted_entities": entities,
                "entity_confidence": entity_confidence,
                "validation_errors": validation_errors,
            },
            "schema_valid": schema_valid,
            "latency_ms": elapsed_ms,
        }
