import io
import logging
from pathlib import Path
from typing import AsyncIterator
from uuid import UUID

from minio import Minio
from minio.error import S3Error
from starlette.concurrency import run_in_threadpool

from ..settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


async def ensure_bucket() -> None:
    exists = await run_in_threadpool(
        minio_client.bucket_exists, settings.minio_bucket
    )
    if not exists:
        await run_in_threadpool(minio_client.make_bucket, settings.minio_bucket)


async def upload_image(
    object_name: str, content: bytes, content_type: str
) -> None:
    try:
        await run_in_threadpool(
            minio_client.put_object,
            settings.minio_bucket,
            object_name,
            io.BytesIO(content),
            len(content),
            content_type=content_type,
        )
    except Exception as exc:
        log.error("Failed to upload to MinIO: %s", exc)
        raise


async def stream_image(
    bucket: str, object_name: str, chunk_size: int = 1024 * 1024
) -> AsyncIterator[bytes]:
    response = await run_in_threadpool(
        minio_client.get_object, bucket, object_name
    )

    async def generator() -> AsyncIterator[bytes]:
        try:
            while True:
                chunk = await run_in_threadpool(response.read, chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            response.close()
            response.release_conn()

    return generator()


def build_object_name(image_id: UUID, filename: str | None) -> str:
    suffix = Path(filename or "").suffix
    return f"{image_id}{suffix}"


def build_preview_name(object_name: str, size: int) -> str:
    path = Path(object_name)
    suffix = path.suffix or ""
    stem = path.stem or "image"
    return f"{stem}_{size}{suffix}"


async def delete_object(bucket: str, object_name: str) -> None:
    try:
        await run_in_threadpool(minio_client.remove_object, bucket, object_name)
    except S3Error as exc:
        if exc.code == "NoSuchKey":
            log.info("Object %s/%s already removed", bucket, object_name)
            return
        log.error("Failed to remove %s/%s: %s", bucket, object_name, exc)
        raise
    except Exception as exc:
        log.error("Failed to remove %s/%s: %s", bucket, object_name, exc)
        raise


async def delete_previews(object_name: str) -> None:
    prefix = f"{Path(object_name).stem}_"
    try:
        objects = await run_in_threadpool(
            lambda: list(
                minio_client.list_objects(
                    settings.preview_bucket, prefix=prefix, recursive=False
                )
            )
        )
        for obj in objects:
            await run_in_threadpool(
                minio_client.remove_object,
                settings.preview_bucket,
                obj.object_name,
            )
    except S3Error as exc:
        if exc.code == "NoSuchBucket":
            log.warning(
                "Preview bucket %s missing; skipping preview cleanup",
                settings.preview_bucket,
            )
            return
        if exc.code == "NoSuchKey":
            log.info("Previews for %s already removed", object_name)
            return
        log.error("Failed to remove previews for %s: %s", object_name, exc)
        raise
    except Exception as exc:
        log.error("Failed to remove previews for %s: %s", object_name, exc)
        raise
