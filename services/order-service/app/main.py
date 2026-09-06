from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session, is_database_ready
from app.repository import create_order, get_order
from app.schemas import CreateOrderRequest, HealthResponse, OrderResponse

SessionDep = Annotated[AsyncSession, Depends(get_session)]

app = FastAPI(
    title="MyService Order API",
    version="0.1.0",
    description="Создание и просмотр заказа в техническом прототипе.",
)


@app.post(
    "/api/v1/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order_endpoint(
    request: CreateOrderRequest,
    session: SessionDep,
) -> OrderResponse:
    order = await create_order(session, request)
    return OrderResponse.model_validate(order)


@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(
    order_id: UUID,
    session: SessionDep,
) -> OrderResponse:
    order = await get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse.model_validate(order)


@app.get("/health/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    return HealthResponse()


@app.get("/health/ready", response_model=HealthResponse)
async def ready(session: SessionDep) -> HealthResponse:
    try:
        await is_database_ready(session)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        ) from None
    return HealthResponse()
