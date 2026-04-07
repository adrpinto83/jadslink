from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan_tier: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
