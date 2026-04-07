from sqlalchemy import String, Integer, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from decimal import Decimal
import uuid


class Plan(BaseModel):
    __tablename__ = "plans"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_bs: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    bandwidth_down_kbps: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # 0 = unlimited
    bandwidth_up_kbps: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    max_devices: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="plans")
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="plan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Plan id={self.id} name={self.name} duration_minutes={self.duration_minutes}>"
