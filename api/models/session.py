from sqlalchemy import String, Boolean, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from datetime import datetime
import uuid


class Session(BaseModel):
    __tablename__ = "sessions"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), unique=True, nullable=False
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False
    )
    device_mac: Mapped[str] = mapped_column(String(17), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bytes_down: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_up: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="session")
    node: Mapped["Node"] = relationship("Node", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session id={self.id} device_mac={self.device_mac} is_active={self.is_active}>"
