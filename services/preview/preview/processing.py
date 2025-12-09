import io
import logging
from typing import Dict

from PIL import Image

log = logging.getLogger(__name__)

CONTENT_TYPE_TO_FORMAT = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/gif": "GIF",
    "image/webp": "WEBP",
    "image/bmp": "BMP",
}


def _resolve_format(content_type: str | None, fallback: str | None) -> str:
    if content_type:
        fmt = CONTENT_TYPE_TO_FORMAT.get(content_type.lower())
        if fmt:
            return fmt
    if fallback:
        return fallback
    return "PNG"


def generate_resized_versions(
    image_bytes: bytes, sizes: list[int], content_type: str | None
) -> Dict[int, bytes]:
    resized: Dict[int, bytes] = {}
    with Image.open(io.BytesIO(image_bytes)) as image:
        output_format = _resolve_format(content_type, image.format)
        for size in sizes:
            if size <= 0:
                log.warning("Skipping non-positive preview size: %s", size)
                continue
            copy = image.copy()
            copy.thumbnail((size, size))
            if output_format.upper() == "JPEG" and copy.mode != "RGB":
                copy = copy.convert("RGB")
            buffer = io.BytesIO()
            save_kwargs: dict[str, object] = {}
            if output_format.upper() == "JPEG":
                save_kwargs["optimize"] = True
                save_kwargs["quality"] = 85
            copy.save(buffer, format=output_format, **save_kwargs)
            resized[size] = buffer.getvalue()
            buffer.close()
            copy.close()
    return resized
