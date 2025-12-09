import logging

from fastapi import FastAPI

from .api import router as api_router
from .http_client import lifespan

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gateway")

app = FastAPI(title="API Gateway", lifespan=lifespan)
app.include_router(api_router)
