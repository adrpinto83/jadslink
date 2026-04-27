"""Schemas for upgrade requests and payments."""

from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
import uuid


class PaymentDetailsBase(BaseModel):
    """Base for payment details"""
    payment_method: Literal["mobile_pay", "gateway"]


class PaymentDetailsPagoMovil(PaymentDetailsBase):
    """Details for Pago Móvil payment"""
    payment_method: Literal["mobile_pay"] = "mobile_pay"
    banco_origen: str = Field(..., description="Banco emisor (BDO, Banesco, etc)")
    cédula_pagador: str = Field(..., description="Cédula del pagador")
    referencia_pago: str = Field(..., description="Referencia de 10 dígitos")
    comprobante_url: Optional[str] = None


class PaymentDetailsCard(PaymentDetailsBase):
    """Details for Card payment"""
    payment_method: Literal["gateway"] = "gateway"
    token: str = Field(..., description="Stripe token")


class UpgradeRequestCreate(BaseModel):
    """Create a new upgrade request"""
    upgrade_type: Literal["extra_tickets", "plan_upgrade"]
    ticket_quantity: Optional[int] = None  # For extra_tickets
    new_plan_tier: Optional[str] = None    # For plan_upgrade (basic, pro)
    payment_method: Literal["mobile_pay", "gateway"]
    payment_details: Optional[dict] = None


class UpgradeRequestResponse(BaseModel):
    """Response for upgrade request"""
    id: uuid.UUID
    tenant_id: uuid.UUID
    upgrade_type: str
    ticket_quantity: Optional[int]
    new_plan_tier: Optional[str]
    payment_method: str
    amount_usd: Decimal
    amount_vef: Optional[Decimal]
    exchange_rate: Optional[Decimal]
    status: str
    banco_origen: Optional[str]
    cédula_pagador: Optional[str]
    referencia_pago: Optional[str]
    comprobante_url: Optional[str]
    últimos_4_digitos: Optional[str]
    reminder_count: int
    created_at: datetime
    updated_at: datetime


class AdminPaymentConfirm(BaseModel):
    """Admin confirms or rejects a payment"""
    action: Literal["approve", "reject"]
    notes: str = Field(..., description="Notas del admin (obligatorio para rechazo)")


class PendingPaymentResponse(BaseModel):
    """Payment pending confirmation"""
    id: uuid.UUID
    tenant_name: str
    contact_email: str
    upgrade_type: str
    amount_usd: Decimal
    amount_vef: Optional[Decimal]
    exchange_rate: Optional[Decimal]
    payment_method: str
    status: str
    banco_origen: Optional[str]
    referencia_pago: Optional[str]
    comprobante_url: Optional[str]
    created_at: datetime
    days_pending: int
    reminder_count: int
