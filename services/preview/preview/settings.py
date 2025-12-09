import json
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import EnvSettingsSource


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PREVIEW_",
    )

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    source_bucket: str = "images"
    preview_bucket: str = "preview"
    minio_secure: bool = False
    rabbitmq_url: str = "amqp://guest:guest@localhost/"
    rabbitmq_queue: str = "image.uploaded"


@lru_cache
def get_settings() -> Settings:
    return Settings()
