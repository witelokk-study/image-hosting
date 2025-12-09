from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from minio.error import S3Error

from ..clients.minio_client import (
    build_object_name,
    build_preview_name,
    stream_image,
    upload_image,
)
from ..db import get_session
from ..messaging import publish_image_uploaded
from ..models import Image
from ..repositories.image_repository import ImageRepository
from ..schemas import ImageResponse
from ..settings import get_settings

router = APIRouter()
settings = get_settings()


@router.post(
    "/images",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image_endpoint(
    file: Annotated[UploadFile, File()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ImageResponse:
    if file.content_type not in settings.allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}",
        )

    contents = await file.read()
    size_bytes = len(contents)
    if size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    image_id = uuid4()
    object_name = build_object_name(image_id, file.filename)

    try:
        await upload_image(object_name, contents, file.content_type)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store image",
        ) from exc

    record = Image(
        id=image_id,
        original_filename=file.filename or "",
        object_name=object_name,
        bucket=settings.minio_bucket,
        content_type=file.content_type,
        size_bytes=size_bytes,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.image_ttl_seconds),
    )

    repo = ImageRepository(session)
    try:
        saved = await repo.add(record)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image metadata",
        ) from exc

    await publish_image_uploaded(
        {
            "id": str(saved.id),
            "original_filename": saved.original_filename,
            "object_name": saved.object_name,
            "bucket": saved.bucket,
            "content_type": saved.content_type,
            "size_bytes": saved.size_bytes,
            "created_at": saved.created_at.isoformat(),
            "expires_at": saved.expires_at.isoformat(),
        }
    )

    return ImageResponse.model_validate(saved)


@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> ImageResponse:
    repo = ImageRepository(session)
    record = await repo.get(image_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return ImageResponse.model_validate(record)


@router.get("/images/{image_id}/file")
async def download_image(
    image_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> StreamingResponse:
    repo = ImageRepository(session)
    record = await repo.get(image_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    stream = await stream_image(record.bucket, record.object_name)

    headers = {
        "Content-Disposition": f'inline; filename="{record.original_filename or record.id}"'
    }
    if record.size_bytes:
        headers["Content-Length"] = str(record.size_bytes)

    return StreamingResponse(stream, media_type=record.content_type, headers=headers)


@router.get("/images/{image_id}/preview/{size}")
async def download_preview(
    image_id: UUID, size: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> StreamingResponse:
    repo = ImageRepository(session)
    record = await repo.get(image_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    preview_name = build_preview_name(record.object_name, size)

    try:
        stream = await stream_image(settings.preview_bucket, preview_name)
    except S3Error as exc:
        if exc.code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Preview not found"
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch preview from storage",
        ) from exc

    headers = {"Content-Disposition": f'inline; filename="{preview_name}"'}

    return StreamingResponse(
        stream,
        media_type=record.content_type or "application/octet-stream",
        headers=headers,
    )
