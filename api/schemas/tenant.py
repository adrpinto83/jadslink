from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantUpdate(BaseModel):
    logo_url: str | None = None
    primary_color: str | None = None
    custom_domain: str | None = None
    ssid: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None

class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan_tier: str
    is_active: bool
    created_at: datetime
    settings: dict | None = {}

    class Config:
        from_attributes = True
