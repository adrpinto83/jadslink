from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class PlanCreate(BaseModel):
    name: str
    duration_minutes: int
    price_usd: Decimal


class PlanUpdate(BaseModel):
    name: str | None = None
    price_usd: Decimal | None = None


class PlanResponse(BaseModel):
    id: UUID
    name: str
    duration_minutes: int
    price_usd: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
