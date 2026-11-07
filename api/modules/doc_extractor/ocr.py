import os
from typing import Any, Protocol

import pytesseract
from PIL import Image
from pytesseract import Output


class OCRProvider(Protocol):

    def extract_text(self, image: Image.Image) -> str:
        ...

    def extract_text_with_confidence(
        self, image: Image.Image
    ) -> dict[str, Any]:
        ...


class TesseractOCR:

    def __init__(self, executable_path: str | None = None):
        path = executable_path or os.getenv("TESSERACT_CMD")

        if path:
            pytesseract.pytesseract.tesseract_cmd = path

    def extract_text(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image)

    def extract_text_with_confidence(
        self, image: Image.Image
    ) -> dict[str, Any]:

        data = pytesseract.image_to_data(
            image,
            output_type=Output.DICT
        )

        words = []

        for index, word in enumerate(data["text"]):
            word = word.strip()

            try:
                confidence = float(data["conf"][index])
            except (ValueError, TypeError):
                continue

            # Ignore empty words and invalid confidence values.
            if not word or confidence < 0:
                continue

            # Extract bounding box coordinates.
            left = int(data["left"][index])
            top = int(data["top"][index])
            width = int(data["width"][index])
            height = int(data["height"][index])

            # Ignore invalid bounding boxes.
            if width <= 0 or height <= 0:
                continue

            words.append({
                "text": word,
                "confidence": round(confidence / 100, 4),
                "bounding_box": {
                    "x_min": left,
                    "y_min": top,
                    "x_max": left + width,
                    "y_max": top + height
                }
            })

        extracted_text = " ".join(
            word["text"] for word in words
        )

        return {
            "text": extracted_text,
            "words": words
        }
