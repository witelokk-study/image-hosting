import asyncio
import json
import logging
from json import JSONDecodeError
from typing import Awaitable, Callable

from .settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

try:
    from aio_pika import IncomingMessage, RobustChannel, RobustConnection, connect_robust
except Exception:  # pragma: no cover - optional dependency
    IncomingMessage = RobustChannel = RobustConnection = connect_robust = None

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


async def _handle_message(
    message: "IncomingMessage",
    handler: Callable[[dict], Awaitable[None]],
) -> None:
    try:
        payload = json.loads(message.body.decode("utf-8"))
    except JSONDecodeError:
        log.error("Discarding message with invalid JSON payload")
        await message.reject(requeue=False)
        return

    try:
        await handler(payload)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # pragma: no cover - runtime path
        log.exception("Failed to process message: %s", exc)
        await message.nack(requeue=False)
    else:
        await message.ack()


async def consume_image_uploaded(
    handler: Callable[[dict], Awaitable[None]]
) -> None:
    if rabbit_channel is None:
        await init_rabbit()

    if rabbit_channel is None:
        log.warning("RabbitMQ channel not initialized; cannot consume messages")
        return

    queue = await rabbit_channel.declare_queue(
        settings.rabbitmq_queue, durable=True
    )

    async with queue.iterator() as iterator:
        async for message in iterator:
            await _handle_message(message, handler)
