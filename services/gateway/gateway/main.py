import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router
from .http_client import lifespan
from .settings import get_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gateway")
settings = get_settings()

app = FastAPI(title="API Gateway", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
