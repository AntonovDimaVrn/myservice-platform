from datetime import UTC, datetime, timedelta

import pytest
from aio_pika import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import OutboxEvent, ServiceType
from app.outbox_worker import publish_pending_once
from app.repository import create_order
from app.schemas import CreateOrderRequest


class RecordingExchange:
    def __init__(self) -> None:
        self.messages: list[tuple[Message, str]] = []

    async def publish(self, message: Message, routing_key: str) -> None:
        self.messages.append((message, routing_key))


class FailingExchange:
    async def publish(self, message: Message, routing_key: str) -> None:
        raise ConnectionError("RabbitMQ is unavailable")


def order_request() -> CreateOrderRequest:
    return CreateOrderRequest(
        serviceType=ServiceType.DISINFECTION,
        customerName="Анна",
        customerPhone="+79991111111",
        address="Москва, улица Мира, дом 5",
        desiredAt=datetime.now(UTC) + timedelta(days=1),
    )


@pytest.mark.asyncio
async def test_worker_marks_event_as_published(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        await create_order(session, order_request())

    exchange = RecordingExchange()
    processed = await publish_pending_once(test_session_factory, exchange, batch_size=10)

    assert processed == 1
    assert len(exchange.messages) == 1
    message, routing_key = exchange.messages[0]
    assert routing_key == "order.created.v1"
    assert b"customerName" not in message.body
    assert b"customerPhone" not in message.body
    assert b"address" not in message.body

    async with test_session_factory() as session:
        event = (await session.scalars(select(OutboxEvent))).one()

    assert event.published_at is not None
    assert event.attempts == 1
    assert event.last_error is None


@pytest.mark.asyncio
async def test_worker_keeps_event_after_publish_error(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        await create_order(session, order_request())

    processed = await publish_pending_once(
        test_session_factory,
        FailingExchange(),
        batch_size=10,
    )

    assert processed == 1

    async with test_session_factory() as session:
        event = (await session.scalars(select(OutboxEvent))).one()

    assert event.published_at is None
    assert event.attempts == 1
    assert event.last_error == "RabbitMQ is unavailable"
