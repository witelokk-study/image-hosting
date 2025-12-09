import asyncio
import logging
from typing import Any

from .clients.minio_client import (
    build_preview_name,
    download_image,
    ensure_bucket,
    upload_preview,
)
from .messaging import close_rabbit, consume_image_uploaded
from .processing import generate_resized_versions
from .settings import get_settings

log = logging.getLogger("preview")
logging.basicConfig(level=logging.INFO)
settings = get_settings()

PREVIEW_SIZES = [256, 512, 1024]


async def handle_image_uploaded(payload: dict[str, Any]) -> None:
    object_name = payload.get("object_name")
    bucket = payload.get("bucket") or settings.source_bucket
    content_type = payload.get("content_type")

    if not object_name:
        raise ValueError("Message missing object_name")

    original_bytes = await download_image(bucket, object_name)
    previews = generate_resized_versions(original_bytes, PREVIEW_SIZES, content_type)
    if not previews:
        log.warning("No previews generated for object %s", object_name)
        return

    for size, content in previews.items():
        preview_name = build_preview_name(object_name, size)
        await upload_preview(
            preview_name, content, content_type or "application/octet-stream"
        )
        log.info(
            "Preview uploaded: %s (%d bytes) for original %s",
            preview_name,
            len(content),
            object_name,
        )


async def main() -> None:
    await ensure_bucket(settings.preview_bucket)
    try:
        await consume_image_uploaded(handle_image_uploaded)
    finally:
        await close_rabbit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
