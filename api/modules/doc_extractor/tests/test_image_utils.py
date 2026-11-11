import base64
import io

import pytest
from fastapi import HTTPException
from modules.doc_extractor.image_utils import decode_document_image
from PIL import Image


def test_empty_image_payload_returns_400():
    with pytest.raises(HTTPException) as exc:
        decode_document_image("")

    assert exc.value.status_code == 400


def test_malformed_base64_returns_422():
    with pytest.raises(HTTPException) as exc:
        decode_document_image("invalid-base64!")

    assert exc.value.status_code == 422


def test_invalid_data_uri_returns_422():
    with pytest.raises(HTTPException) as exc:
        decode_document_image("data:image/png;base64")

    assert exc.value.status_code == 422


def test_unsupported_image_format_returns_422():
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, format="GIF")
    encoded = base64.b64encode(buffer.getvalue()).decode()

    with pytest.raises(HTTPException) as exc:
        decode_document_image(encoded)

    assert exc.value.status_code == 422


def test_corrupted_image_returns_422():
    encoded = base64.b64encode(b"not-an-image").decode()

    with pytest.raises(HTTPException) as exc:
        decode_document_image(encoded)

    assert exc.value.status_code == 422
