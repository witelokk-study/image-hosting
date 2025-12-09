import pytest

from storage.settings import Settings


def _build_settings(**overrides: object) -> Settings:
    base = {
        "database_url": "sqlite+aiosqlite://",
        "minio_endpoint": "localhost:9000",
        "minio_access_key": "access",
        "minio_secret_key": "secret",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_allowed_content_types_parsed_from_string() -> None:
    settings = _build_settings(
        allowed_content_types="image/jpeg, image/png,  image/gif "
    )

    assert settings.allowed_content_types == [
        "image/jpeg",
        "image/png",
        "image/gif",
    ]


def test_allowed_content_types_accepts_list() -> None:
    values = ["image/jpeg", "image/png"]
    settings = _build_settings(allowed_content_types=values)
    assert settings.allowed_content_types == values


@pytest.mark.parametrize("field", ["image_ttl_seconds", "cleanup_interval_seconds"])
def test_numeric_fields_must_be_positive(field: str) -> None:
    with pytest.raises(ValueError):
        _build_settings(**{field: 0})

