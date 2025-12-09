import asyncio
import json
import os

import pytest

# Provide minimal settings so preview.settings.Settings can be constructed
os.environ.setdefault("PREVIEW_MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("PREVIEW_MINIO_ACCESS_KEY", "test-access-key")
os.environ.setdefault("PREVIEW_MINIO_SECRET_KEY", "test-secret-key")

from preview.messaging import _handle_message


class DummyMessage:
    def __init__(self, body: bytes):
        self.body = body
        self.acked = False
        self.nacked = False
        self.rejected = False
        self.nack_kwargs: dict | None = None
        self.reject_kwargs: dict | None = None

    async def ack(self) -> None:
        self.acked = True

    async def nack(self, *, requeue: bool = False) -> None:
        self.nacked = True
        self.nack_kwargs = {"requeue": requeue}

    async def reject(self, *, requeue: bool = False) -> None:
        self.rejected = True
        self.reject_kwargs = {"requeue": requeue}


def test_handle_message_ack_on_success() -> None:
    payload = {"id": "123"}
    message = DummyMessage(json.dumps(payload).encode("utf-8"))

    captured: dict | None = None

    async def handler(data: dict) -> None:
        nonlocal captured
        captured = data

    asyncio.run(_handle_message(message, handler))

    assert captured == payload
    assert message.acked is True
    assert message.nacked is False
    assert message.rejected is False


def test_handle_message_rejects_on_invalid_json() -> None:
    message = DummyMessage(b"{invalid json")

    async def handler(_: dict) -> None:
        raise AssertionError("Handler should not be called")

    asyncio.run(_handle_message(message, handler))

    assert message.rejected is True
    assert message.reject_kwargs == {"requeue": False}
    assert message.acked is False
    assert message.nacked is False


def test_handle_message_nacks_on_handler_exception() -> None:
    payload = {"id": "123"}
    message = DummyMessage(json.dumps(payload).encode("utf-8"))

    async def handler(_: dict) -> None:
        raise RuntimeError("boom")

    asyncio.run(_handle_message(message, handler))

    assert message.nacked is True
    assert message.nack_kwargs == {"requeue": False}
    assert message.acked is False
    assert message.rejected is False


def test_handle_message_propagates_cancelled_error() -> None:
    payload = {"id": "123"}
    message = DummyMessage(json.dumps(payload).encode("utf-8"))

    async def handler(_: dict) -> None:
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(_handle_message(message, handler))
