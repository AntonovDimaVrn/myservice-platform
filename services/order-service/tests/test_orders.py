from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import OutboxEvent


def valid_order() -> dict[str, str]:
    return {
        "serviceType": "dry_cleaning",
        "customerName": "Иван",
        "customerPhone": "+79990000000",
        "address": "Москва, улица Ленина, дом 10",
        "desiredAt": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
        "comment": "Диван, три места",
    }


@pytest.mark.asyncio
async def test_create_and_get_order(
    client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    create_response = await client.post("/api/v1/orders", json=valid_order())

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "new"
    assert created["serviceType"] == "dry_cleaning"

    get_response = await client.get(f"/api/v1/orders/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == created

    async with test_session_factory() as session:
        event = (await session.scalars(select(OutboxEvent))).one()

    assert event.aggregate_id.hex == created["id"].replace("-", "")
    assert event.routing_key == "order.created.v1"
    assert set(event.payload) == {
        "eventId",
        "eventType",
        "eventVersion",
        "occurredAt",
        "orderId",
        "serviceType",
        "status",
    }
    assert "Иван" not in str(event.payload)
    assert "+79990000000" not in str(event.payload)
    assert "Ленина" not in str(event.payload)


@pytest.mark.asyncio
async def test_unknown_order_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/orders/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("customerPhone", "89990000000"),
        ("customerName", "A"),
        ("address", "Дом"),
        ("desiredAt", "2020-01-01T10:00:00+00:00"),
    ],
)
async def test_invalid_order_returns_422(
    client: AsyncClient,
    field: str,
    value: str,
) -> None:
    request = valid_order()
    request[field] = value

    response = await client.post("/api/v1/orders", json=request)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient) -> None:
    live_response = await client.get("/health/live")
    ready_response = await client.get("/health/ready")

    assert live_response.status_code == 200
    assert ready_response.status_code == 200
    assert live_response.json() == {"status": "ok"}
    assert ready_response.json() == {"status": "ok"}
