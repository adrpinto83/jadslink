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


class GrantFreeSubscriptionRequest(BaseModel):
    plan: str  # 'pro', 'basic', etc
    days: int  # Cuántos días de acceso gratuito
    reason: str | None = None  # Razón (ej: "prueba", "promoción")


class SubscriptionInfo(BaseModel):
    plan_tier: str
    subscription_status: str
    free_subscription_until: datetime | None = None
    free_subscription_plan: str | None = None
    free_subscription_reason: str | None = None
    is_free_subscription_active: bool

    class Config:
        from_attributes = True
