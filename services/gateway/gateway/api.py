from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from httpx import AsyncClient, Response

from .http_client import get_http_client
router = APIRouter()


async def _proxied_stream(response: Response):
    try:
        async for chunk in response.aiter_bytes():
            yield chunk
    finally:
        await response.aclose()


async def _stream_request(
    client: AsyncClient, method: str, url: str
) -> Response:
    request = client.build_request(method, url)
    return await client.send(request, stream=True)


@router.post(
    "/images",
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    file: Annotated[UploadFile, File()],
    client: Annotated[AsyncClient, Depends(get_http_client)],
):
    payload = {
        "file": (
            file.filename,
            await file.read(),
            file.content_type or "application/octet-stream",
        )
    }

    response = await client.post("/images", files=payload)
    if response.is_error:
        detail = response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") else response.text
        raise HTTPException(
            status_code=response.status_code,
            detail=detail or "Failed to upload image",
        )
    return response.json()


@router.get("/images/{image_id}")
async def get_image(
    image_id: UUID,
    client: Annotated[AsyncClient, Depends(get_http_client)],
):
    response = await client.get(f"/images/{image_id}")
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    if response.is_error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch image metadata",
        )
    return response.json()


@router.get("/images/{image_id}/file")
async def download_image(
    image_id: UUID,
    client: Annotated[AsyncClient, Depends(get_http_client)],
):
    response = await _stream_request(client, "GET", f"/images/{image_id}/file")
    if response.status_code == status.HTTP_404_NOT_FOUND:
        await response.aclose()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    if response.is_error:
        detail = (
            (await response.json()).get("detail")
            if response.headers.get("content-type", "").startswith("application/json")
            else await response.aread()
        )
        await response.aclose()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail or "Failed to download image",
        )

    headers = {}
    content_type = response.headers.get("content-type")
    if content_type:
        headers["Content-Type"] = content_type
    content_disposition = response.headers.get("content-disposition")
    if content_disposition:
        headers["Content-Disposition"] = content_disposition
    content_length = response.headers.get("content-length")
    if content_length:
        headers["Content-Length"] = content_length

    return StreamingResponse(
        _proxied_stream(response),
        media_type=content_type,
        headers=headers,
    )


@router.get("/images/{image_id}/preview/{size}")
async def get_preview(
    image_id: UUID,
    size: int,
    client: Annotated[AsyncClient, Depends(get_http_client)],
):
    response = await _stream_request(
        client, "GET", f"/images/{image_id}/preview/{size}"
    )
    if response.status_code == status.HTTP_404_NOT_FOUND:
        await response.aclose()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preview not found"
        )
    if response.is_error:
        detail = (
            (await response.json()).get("detail")
            if response.headers.get("content-type", "").startswith("application/json")
            else await response.aread()
        )
        await response.aclose()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail or "Failed to fetch preview",
        )

    headers = {}
    content_type = response.headers.get("content-type")
    if content_type:
        headers["Content-Type"] = content_type
    content_disposition = response.headers.get("content-disposition")
    if content_disposition:
        headers["Content-Disposition"] = content_disposition
    content_length = response.headers.get("content-length")
    if content_length:
        headers["Content-Length"] = content_length

    return StreamingResponse(
        _proxied_stream(response),
        media_type=content_type,
        headers=headers,
    )
