from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import AbstractExchange
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.database import session_factory
from app.models import OutboxEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def publish_pending_once(
    factory: async_sessionmaker[AsyncSession],
    exchange: AbstractExchange,
    batch_size: int,
) -> int:
    statement = (
        select(OutboxEvent)
        .where(OutboxEvent.published_at.is_(None))
        .order_by(OutboxEvent.created_at)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )

    async with factory() as session, session.begin():
        events = list((await session.scalars(statement)).all())

        for event in events:
            message = Message(
                body=json.dumps(event.payload, ensure_ascii=False).encode(),
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=str(event.id),
                type=event.event_type,
            )
            try:
                await exchange.publish(message, routing_key=event.routing_key)
            except Exception as error:
                event.attempts += 1
                event.last_error = str(error)[:500]
                logger.warning("Outbox event %s was not published", event.id)
                continue

            event.published_at = datetime.now(UTC)
            event.attempts += 1
            event.last_error = None
            logger.info("Outbox event %s was published", event.id)

    return len(events)


async def run() -> None:
    settings = get_settings()
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)

    async with connection:
        channel = await connection.channel(publisher_confirms=True)
        exchange = await channel.declare_exchange(
            settings.rabbitmq_exchange,
            ExchangeType.TOPIC,
            durable=True,
        )

        logger.info("Outbox worker started")
        while True:
            await publish_pending_once(session_factory, exchange, settings.outbox_batch_size)
            await asyncio.sleep(settings.outbox_poll_interval)


if __name__ == "__main__":
    asyncio.run(run())
