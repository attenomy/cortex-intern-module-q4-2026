from unittest.mock import patch

from PIL import Image
from pytesseract import Output

from modules.doc_extractor.ocr import TesseractOCR


def test_tesseract_ocr_extracts_text():
    image = Image.new("RGB", (100, 100), color="white")

    with patch(
        "modules.doc_extractor.ocr.pytesseract.image_to_string",
        return_value="Invoice Number: INV-101"
    ) as mock_ocr:

        ocr = TesseractOCR()
        result = ocr.extract_text(image)

        assert result == "Invoice Number: INV-101"
        mock_ocr.assert_called_once_with(image)


def test_tesseract_ocr_returns_empty_text():
    image = Image.new("RGB", (100, 100), color="white")

    with patch(
        "modules.doc_extractor.ocr.pytesseract.image_to_string",
        return_value=""
    ):
        ocr = TesseractOCR()
        result = ocr.extract_text(image)

        assert result == ""


def test_tesseract_ocr_extracts_bounding_boxes():
    image = Image.new("RGB", (300, 100), color="white")

    mock_data = {
        "text": ["Invoice", "12345"],
        "conf": ["95", "90"],
        "left": [10, 100],
        "top": [20, 20],
        "width": [60, 50],
        "height": [25, 25]
    }

    with patch(
        "modules.doc_extractor.ocr.pytesseract.image_to_data",
        return_value=mock_data
    ) as mock_ocr:

        ocr = TesseractOCR()
        result = ocr.extract_text_with_confidence(image)

        mock_ocr.assert_called_once_with(
            image,
            output_type=Output.DICT
        )

        assert result["text"] == "Invoice 12345"
        assert len(result["words"]) == 2

        first_word = result["words"][0]

        assert first_word["text"] == "Invoice"
        assert first_word["confidence"] == 0.95

        assert first_word["bounding_box"] == {
            "x_min": 10,
            "y_min": 20,
            "x_max": 70,
            "y_max": 45
        }

        for word in result["words"]:
            box = word["bounding_box"]

            assert box["x_min"] < box["x_max"]
            assert box["y_min"] < box["y_max"]
            assert 0 <= word["confidence"] <= 1