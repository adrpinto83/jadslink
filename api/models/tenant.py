from sqlalchemy import String, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel
import enum


class PlanTier(str, enum.Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


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

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug} plan_tier={self.plan_tier}>"
