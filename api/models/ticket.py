from sqlalchemy import String, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from datetime import datetime
import enum
import uuid


class TicketStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    revoked = "revoked"


class Ticket(BaseModel):
    __tablename__ = "tickets"

    code: Mapped[str] = mapped_column(
        String(8), unique=True, nullable=False, index=True
    )
    qr_data: Mapped[str] = mapped_column(String(500), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False
    )
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus), default=TicketStatus.pending, nullable=False
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    device_mac: Mapped[str | None] = mapped_column(String(17), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="tickets")
    node: Mapped["Node"] = relationship("Node", back_populates="tickets")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="tickets")
    session: Mapped["Session"] = relationship(
        "Session", back_populates="ticket", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} code={self.code} status={self.status}>"
