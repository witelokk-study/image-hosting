from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "images"
    preview_bucket: str = "preview"
    minio_secure: bool = False
    rabbitmq_url: str = "amqp://guest:guest@localhost/"
    allowed_content_types: List[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/bmp",
    ]
    image_ttl_seconds: int = 24 * 60 * 60
    cleanup_interval_seconds: int = 5 * 60

    class Config:
        env_prefix = "STORAGE_"

    @field_validator("allowed_content_types", mode="before")
    @classmethod
    def split_content_types(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("image_ttl_seconds", "cleanup_interval_seconds")
    @classmethod
    def validate_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Must be a positive integer")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
