import base64
import binascii
import io

from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException


SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


def decode_document_image(image_base64: str) -> Image.Image:
    """
    Decode and validate a Base64 document image.
    """

    if not image_base64 or not image_base64.strip():
        raise HTTPException(
            status_code=400,
            detail="Image payload cannot be empty"
        )

    if image_base64.startswith("data:"):
        try:
            image_base64 = image_base64.split(",", 1)[1]
        except IndexError:
            raise HTTPException(
                status_code=422,
                detail="Invalid image data URI"
            )

    try:
        image_bytes = base64.b64decode(
            image_base64,
            validate=True
        )
    except (binascii.Error, ValueError):
        raise HTTPException(
            status_code=422,
            detail="Malformed Base64 image data"
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))

        if image.format not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=422,
                detail="Unsupported image format"
            )

        image.verify()

        image = Image.open(io.BytesIO(image_bytes))
        image.load()

        return image.convert("RGB")

    except HTTPException:
        raise

    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="Invalid or corrupted image"
        )