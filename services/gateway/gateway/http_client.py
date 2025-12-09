from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from httpx import AsyncClient

from .settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create a single shared HTTP client for proxying to the storage service."""
    async with AsyncClient(
        base_url=settings.storage_base_url,
        timeout=None,
    ) as client:
        app.state.http_client = client
        yield


def get_http_client(request: Request) -> AsyncClient:
    return request.app.state.http_client
