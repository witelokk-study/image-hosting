import base64
import os
import time
from typing import Final

import requests


BASE_URL: Final = os.getenv("STORAGE_BASE_URL", "http://localhost:8000")

# Minimal 1x1 PNG image (opaque white)
_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
    "ASsJTYQAAAAASUVORK5CYII="
)
PNG_BYTES: Final[bytes] = base64.b64decode(_PNG_BASE64)


def _wait_for_service(timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = requests.get(f"{BASE_URL}/docs", timeout=5)
            if response.status_code == 200:
                return
        except Exception as exc:  # pragma: no cover - diagnostic path
            last_error = exc
        time.sleep(2)
    raise RuntimeError(f"Storage service not ready: {last_error}")


def test_upload_and_download_image() -> None:
    _wait_for_service()

    # Upload an image
    files = {"file": ("test.png", PNG_BYTES, "image/png")}
    response = requests.post(f"{BASE_URL}/images", files=files, timeout=10)
    assert response.status_code == 201
    data = response.json()

    image_id = data["id"]
    assert image_id
    assert data["content_type"] == "image/png"
    assert data["size_bytes"] == len(PNG_BYTES)

    # Fetch metadata
    meta = requests.get(f"{BASE_URL}/images/{image_id}", timeout=10)
    assert meta.status_code == 200
    meta_data = meta.json()
    assert meta_data["id"] == image_id
    assert meta_data["object_name"]

    # Download the file
    download = requests.get(f"{BASE_URL}/images/{image_id}/file", timeout=10)
    assert download.status_code == 200
    assert download.headers.get("content-type", "").startswith("image/")
    assert download.content == PNG_BYTES

