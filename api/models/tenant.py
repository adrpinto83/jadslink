from sqlalchemy import String, Boolean, Enum as SQLEnum, JSON, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel
import enum
from datetime import datetime
from typing import Optional


class PlanTier(str, enum.Enum):
    free = "free"        # Gratuito: 1 nodo, 50 tickets/mes
    basic = "basic"      # Básico: $29/mes, 200 tickets, 1 nodo
    standard = "standard"  # Estándar: $79/mes, 1,000 tickets, 3 nodos
    pro = "pro"          # Pro: $199/mes, ilimitado


class SubscriptionStatus(str, enum.Enum):
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    unpaid = "unpaid"


class Tenant(BaseModel):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Subscription details
    plan_tier: Mapped[PlanTier] = mapped_column(
        SQLEnum(PlanTier, name="plantier"), default=PlanTier.free, nullable=False
    )
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus, name="subscriptionstatus"),
        default=SubscriptionStatus.trialing,
        nullable=False,
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=True
    )

    # Free/Pro subscriptions granted by superadmin
    free_subscription_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # Cuándo vence la suscripción gratuita pro
    free_subscription_plan: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Qué plan se otorgó gratuitamente (pro, basic, etc)
    free_subscription_reason: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Razón por la cual se otorgó (prueba, promoción, etc)

    # Tracking para planes free y basic
    free_tickets_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    free_tickets_limit: Mapped[int] = mapped_column(Integer, default=50, nullable=False)  # 50 tickets de prueba
    extra_tickets_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Múltiplos de 50 pagos

    # Settings
    settings: Mapped[dict] = mapped_column(
        JSON,
        default={
            "logo_url": None,
            "primary_color": "#2563eb",
            "payment_methods": ["cash"],
            "ssid": None,
            "contact_email": None,
            "contact_phone": None,
        },
        nullable=True,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="tenant", foreign_keys="User.tenant_id"
    )
    nodes: Mapped[list["Node"]] = relationship(
        "Node", back_populates="tenant", cascade="all, delete-orphan"
    )
    plans: Mapped[list["Plan"]] = relationship(
        "Plan", back_populates="tenant", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="tenant", cascade="all, delete-orphan"
    )

    def get_max_nodes(self) -> int:
        """Retorna el máximo número de nodos según el plan"""
        if self.plan_tier == PlanTier.free or self.plan_tier == PlanTier.basic:
            return 1
        elif self.plan_tier == PlanTier.standard:
            return 3
        return 999999  # Pro tiene ilimitados

    def get_available_tickets(self) -> int:
        """Retorna cuántos tickets puede generar sin costo adicional"""
        if self.plan_tier == PlanTier.free:
            return max(0, self.free_tickets_limit - self.free_tickets_used)
        elif self.plan_tier == PlanTier.basic:
            return max(0, self.free_tickets_limit - self.free_tickets_used)
        return 999999  # Pro es ilimitado

    def get_total_available_tickets(self) -> int:
        """Retorna tickets gratuitos + pagos disponibles"""
        free_available = self.get_available_tickets()
        if self.plan_tier in [PlanTier.free, PlanTier.basic]:
            paid_available = self.extra_tickets_count * 50
            return free_available + paid_available
        return 999999

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug} plan_tier={self.plan_tier}>"
