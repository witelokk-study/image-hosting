import json
import logging
from typing import Any

from .settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

try:
    from aio_pika import Message, RobustChannel, RobustConnection, connect_robust
except Exception:  # pragma: no cover - optional at import time
    Message = None
    RobustChannel = RobustConnection = None
    connect_robust = None


rabbit_connection: RobustConnection | None = None
rabbit_channel: RobustChannel | None = None


async def init_rabbit() -> None:
    global rabbit_channel, rabbit_connection
    if connect_robust is None:
        log.warning("aio-pika not available; skipping rabbitmq connection")
        return
    rabbit_connection = await connect_robust(settings.rabbitmq_url)
    rabbit_channel = await rabbit_connection.channel()


async def close_rabbit() -> None:
    if rabbit_connection:
        await rabbit_connection.close()


async def publish_image_uploaded(payload: dict[str, Any]) -> None:
    if rabbit_channel is None or Message is None:
        log.warning("RabbitMQ channel not initialized; skipping publish")
        return
    body = json.dumps(payload).encode("utf-8")
    try:
        await rabbit_channel.default_exchange.publish(
            Message(body=body, content_type="application/json"),
            routing_key="image.uploaded",
        )
    except Exception as exc:  # pragma: no cover - side effect with broker
        log.error("Failed to publish event: %s", exc)
