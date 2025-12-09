import asyncio
import logging
from datetime import datetime, timezone

from .clients.minio_client import delete_object, delete_previews
from .db import async_session
from .models import Image
from .repositories.image_repository import ImageRepository
from .settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

_cleanup_task: asyncio.Task | None = None


async def cleanup_expired_once() -> None:
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        repo = ImageRepository(session)
        expired = await repo.list_expired(now)

        for image in expired:
            await _delete_image(repo, image)


async def _delete_image(repo: ImageRepository, image: Image) -> None:
    try:
        await delete_object(image.bucket, image.object_name)
    except Exception:
        log.warning(
            "Failed to delete object %s/%s; keeping metadata for retry",
            image.bucket,
            image.object_name,
        )
        return

    try:
        await delete_previews(image.object_name)
    except Exception:
        log.warning(
            "Failed to delete previews for %s; keeping metadata for retry",
            image.object_name,
        )
        return

    try:
        await repo.delete(image)
        log.info("Expired image %s deleted", image.id)
    except Exception as exc:
        await repo.session.rollback()
        log.error("Failed to delete image metadata %s: %s", image.id, exc)


async def _cleanup_loop() -> None:
    while True:
        try:
            await asyncio.sleep(settings.cleanup_interval_seconds)
            await cleanup_expired_once()
        except asyncio.CancelledError:
            break
        except Exception:
            log.exception("Error during cleanup job")


async def start_cleanup_task() -> None:
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_cleanup_loop())


async def stop_cleanup_task() -> None:
    global _cleanup_task
    if _cleanup_task is not None:
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        _cleanup_task = None
