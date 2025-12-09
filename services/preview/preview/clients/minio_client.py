import asyncio
import io
import logging
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from ..settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


async def ensure_bucket(bucket: str) -> None:
    exists = await asyncio.to_thread(minio_client.bucket_exists, bucket)
    if not exists:
        await asyncio.to_thread(minio_client.make_bucket, bucket)


async def download_image(bucket: str, object_name: str) -> bytes:
    response = await asyncio.to_thread(
        minio_client.get_object, bucket, object_name
    )
    try:
        return await asyncio.to_thread(response.read)
    finally:
        response.close()
        response.release_conn()


async def upload_preview(
    object_name: str, content: bytes, content_type: str
) -> None:
    try:
        await asyncio.to_thread(
            minio_client.put_object,
            settings.preview_bucket,
            object_name,
            io.BytesIO(content),
            len(content),
            content_type=content_type,
        )
    except S3Error as exc:  # pragma: no cover - network side effect
        log.error("Failed to upload preview to MinIO: %s", exc)
        raise


def build_preview_name(object_name: str, size: int) -> str:
    path = Path(object_name)
    suffix = path.suffix or ""
    stem = path.stem or "image"
    return f"{stem}_{size}{suffix}"
