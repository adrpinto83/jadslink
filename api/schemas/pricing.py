"""Schemas for pricing configuration."""

from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime


class PricingConfigUpdate(BaseModel):
    """Schema for updating pricing configuration"""
    ticket_pack_size: int | None = Field(None, ge=1)
    ticket_pack_price_usd: Decimal | None = Field(None, ge=Decimal("0.01"))
    additional_node_price_usd: Decimal | None = Field(None, ge=Decimal("0.01"))
    free_plan_max_nodes: int | None = Field(None, ge=1)
    free_plan_max_tickets: int | None = Field(None, ge=1)
    basic_plan_max_nodes: int | None = Field(None, ge=1)
    basic_plan_max_free_tickets: int | None = Field(None, ge=1)
    description: str | None = Field(None, max_length=500)


class PricingConfigResponse(BaseModel):
    """Schema for pricing configuration response"""
    id: UUID
    ticket_pack_size: int
    ticket_pack_price_usd: Decimal
    additional_node_price_usd: Decimal
    free_plan_max_nodes: int
    free_plan_max_tickets: int
    basic_plan_max_nodes: int
    basic_plan_max_free_tickets: int
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
