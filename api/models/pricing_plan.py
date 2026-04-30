from sqlalchemy import String, Numeric, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class PricingPlan(BaseModel):
    """Modelo para los planes SaaS ofrecidos en JADSlink"""

    __tablename__ = "pricing_plans"

    # Identificador del plan
    tier: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Precios
    monthly_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )  # 0, 29, 79, 199

    # Tickets incluidos
    included_tickets_per_month: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 50, 200, 1000, 999999
    additional_ticket_pack_size: Mapped[int] = mapped_column(
        Integer, default=100, nullable=False
    )
    additional_ticket_pack_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # NULL si no hay opción de comprar adicionales
    is_tickets_unlimited: Mapped[bool] = mapped_column(Boolean, default=False)

    # Nodos incluidos
    included_nodes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    additional_node_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # NULL si no hay opción de agregar nodos
    is_nodes_unlimited: Mapped[bool] = mapped_column(Boolean, default=False)

    # Features
    has_api_access: Mapped[bool] = mapped_column(Boolean, default=False)
    api_access_level: Mapped[str] = mapped_column(
        String(50), default="none", nullable=False
    )  # none, basic, full
    support_level: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # email_48h, email_24h, chat_12h, phone_24_7
    reports_level: Mapped[str] = mapped_column(
        String(50), default="basic", nullable=False
    )  # basic, advanced, custom
    data_retention_days: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )  # 30, 90, 365, -1 (unlimited)

    # UI
    icon: Mapped[str] = mapped_column(String(50), default="wifi", nullable=False)
    color: Mapped[str] = mapped_column(String(50), default="blue", nullable=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True, nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<PricingPlan tier={self.tier} name={self.name} price=${self.monthly_price}/mes>"
