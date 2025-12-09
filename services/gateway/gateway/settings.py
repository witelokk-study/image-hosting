from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration for the API Gateway."""

    storage_base_url: str = "http://storage:8000"
    allowed_origins: list[str] = ["*"]

    class Config:
        env_prefix = "GATEWAY_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
