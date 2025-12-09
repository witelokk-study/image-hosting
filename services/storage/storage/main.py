import logging

from fastapi import FastAPI

from .api.images import router as images_router
from .clients.minio_client import ensure_bucket
from .db import engine, init_models
from .messaging import close_rabbit, init_rabbit

log = logging.getLogger("storage")

app = FastAPI(title="Storage Service")
app.include_router(images_router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_models()
    await ensure_bucket()
    await init_rabbit()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_rabbit()
    await engine.dispose()
