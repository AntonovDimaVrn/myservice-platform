from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderStatus, OutboxEvent, utc_now
from app.schemas import CreateOrderRequest


async def create_order(session: AsyncSession, request: CreateOrderRequest) -> Order:
    now = utc_now()
    order_id = uuid4()
    event_id = uuid4()

    order = Order(
        id=order_id,
        service_type=request.service_type,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        address=request.address,
        desired_at=request.desired_at,
        comment=request.comment,
        status=OrderStatus.NEW,
        created_at=now,
        updated_at=now,
    )
    event = OutboxEvent(
        id=event_id,
        aggregate_type="order",
        aggregate_id=order_id,
        event_type="order.created",
        routing_key="order.created.v1",
        payload={
            "eventId": str(event_id),
            "eventType": "order.created",
            "eventVersion": 1,
            "occurredAt": now.isoformat(),
            "orderId": str(order_id),
            "serviceType": request.service_type.value,
            "status": OrderStatus.NEW.value,
        },
        created_at=now,
    )

    async with session.begin():
        session.add(order)
        session.add(event)

    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: UUID) -> Order | None:
    return await session.get(Order, order_id)
