"""Model for subscription upgrade and payment requests."""

from sqlalchemy import String, Integer, Numeric, Boolean, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from decimal import Decimal
from typing import Any
import uuid
import enum


class PaymentMethod(str, enum.Enum):
    """Métodos de pago disponibles en Venezuela"""
    cash = "cash"                    # Efectivo
    mobile_pay = "mobile_pay"        # Pago Móvil (Transferencia bancaria)
    gateway = "gateway"              # Pasarela (Tarjeta de crédito/débito)


class UpgradeType(str, enum.Enum):
    """Tipos de solicitud de upgrade"""
    extra_tickets = "extra_tickets"  # Comprar 50 tickets adicionales
    plan_upgrade = "plan_upgrade"    # Cambiar a plan pagado (basic/pro)


class PaymentStatus(str, enum.Enum):
    """Estados del pago"""
    pending_payment = "pending_payment"      # Esperando que pague
    payment_received = "payment_received"    # Admin vio el pago
    approved = "approved"                    # Admin aprobó
    rejected = "rejected"                    # Admin rechazó
    cancelled = "cancelled"                  # Cliente canceló


class UpgradeRequest(BaseModel):
    """Solicitud de cambio de plan o compra de tickets adicionales"""
    __tablename__ = "upgrade_requests"

    # Relación con tenant
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )

    # Tipo de solicitud
    upgrade_type: Mapped[UpgradeType] = mapped_column(
        SQLEnum(UpgradeType, name="upgradetype"), nullable=False
    )

    # Para extra_tickets: cuántos paquetes de 50
    ticket_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Para plan_upgrade: a qué plan
    new_plan_tier: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Método de pago elegido
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod, name="paymentmethod"), nullable=False
    )

    # Montos
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_vef: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    exchange_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)  # Tasa oficial del día

    # Estado del pago
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name="paymentstatus"),
        default=PaymentStatus.pending_payment,
        nullable=False
    )

    # Detalles del pago (según método)
    payment_details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # JSON con datos específicos

    # Para Pago Móvil
    banco_origen: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cédula_pagador: Mapped[str | None] = mapped_column(String(20), nullable=True)
    referencia_pago: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comprobante_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Para Tarjeta
    últimos_4_digitos: Mapped[str | None] = mapped_column(String(4), nullable=True)

    # Notas y auditoría
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Email del admin

    # Recordatorios
    reminder_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reminder_at: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id])

    def __repr__(self) -> str:
        return f"<UpgradeRequest id={self.id} tenant_id={self.tenant_id} type={self.upgrade_type} status={self.status}>"
