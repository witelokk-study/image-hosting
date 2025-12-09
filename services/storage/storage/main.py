import logging

from fastapi import FastAPI

from .api.images import router as images_router
from .cleanup import start_cleanup_task, stop_cleanup_task
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
    await start_cleanup_task()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await stop_cleanup_task()
    await close_rabbit()
    await engine.dispose()
