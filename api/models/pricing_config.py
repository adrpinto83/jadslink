"""Global pricing configuration for the platform."""

from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel
from decimal import Decimal


class PricingConfig(BaseModel):
    """Global pricing configuration - managed by superadmin only"""
    __tablename__ = "pricing_configs"

    # Ticket pricing
    ticket_pack_size: Mapped[int] = mapped_column(default=50, nullable=False)
    ticket_pack_price_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.50"), nullable=False
    )

    # Node pricing (for paid additional nodes)
    additional_node_price_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("50.00"), nullable=False
    )

    # Free plan limits
    free_plan_max_nodes: Mapped[int] = mapped_column(default=1, nullable=False)
    free_plan_max_tickets: Mapped[int] = mapped_column(default=50, nullable=False)

    # Basic plan limits
    basic_plan_max_nodes: Mapped[int] = mapped_column(default=1, nullable=False)
    basic_plan_max_free_tickets: Mapped[int] = mapped_column(default=50, nullable=False)

    description: Mapped[str] = mapped_column(
        String(500), default="Default pricing configuration", nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<PricingConfig "
            f"ticket_pack=${self.ticket_pack_price_usd}/{self.ticket_pack_size} "
            f"additional_node=${self.additional_node_price_usd}>"
        )
