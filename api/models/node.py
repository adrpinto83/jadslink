from sqlalchemy import String, Boolean, Enum as SQLEnum, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from datetime import datetime
import enum
import uuid
from typing import Optional


class NodeStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    degraded = "degraded"


class Node(BaseModel):
    __tablename__ = "nodes"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    serial: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    location: Mapped[dict] = mapped_column(
        JSON,
        default={"lat": None, "lng": None, "address": "", "description": ""},
        nullable=True,
    )
    status: Mapped[NodeStatus] = mapped_column(
        SQLEnum(NodeStatus), default=NodeStatus.offline, nullable=False
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    wan_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    config: Mapped[dict] = mapped_column(
        JSON,
        default={
            # WiFi Configuration
            "ssid": "JADSlink",
            "channel": 6,
            "max_clients": 10,
            "bandwidth_default": 2000,
            # Router Communication
            "api_endpoint": "https://api.jadslink.io",
            "heartbeat_interval": 30,
            "metrics_interval": 60,
            "enable_metrics": True,
        },
        nullable=True,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="nodes")
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="node", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="node", cascade="all, delete-orphan"
    )
    metrics: Mapped[list["NodeMetric"]] = relationship(
        "NodeMetric", back_populates="node", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Node id={self.id} name={self.name} status={self.status}>"
