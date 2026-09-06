from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import OrderStatus, ServiceType


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class OrderFields(ApiModel):
    service_type: ServiceType
    customer_name: str = Field(min_length=2, max_length=120)
    customer_phone: str = Field(pattern=r"^\+[1-9][0-9]{7,14}$")
    address: str = Field(min_length=5, max_length=500)
    desired_at: datetime
    comment: str | None = Field(default=None, max_length=1000)


class CreateOrderRequest(OrderFields):
    @field_validator("desired_at")
    @classmethod
    def validate_desired_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("desiredAt must contain a timezone")
        if value <= datetime.now(UTC):
            raise ValueError("desiredAt must be in the future")
        return value


class OrderResponse(OrderFields):
    id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class HealthResponse(ApiModel):
    status: str = "ok"
