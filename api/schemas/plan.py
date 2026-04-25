from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class PlanCreate(BaseModel):
    name: str
    duration_minutes: int
    price_usd: Decimal
    bandwidth_down_kbps: int = 0
    bandwidth_up_kbps: int = 0
    max_devices: int = 1
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: str | None = None
    duration_minutes: int | None = None
    price_usd: Decimal | None = None
    bandwidth_down_kbps: int | None = None
    bandwidth_up_kbps: int | None = None
    max_devices: int | None = None
    is_active: bool | None = None


class PlanResponse(BaseModel):
    id: UUID
    name: str
    duration_minutes: int
    price_usd: Decimal
    bandwidth_down_kbps: int
    bandwidth_up_kbps: int
    max_devices: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
