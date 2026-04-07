from sqlalchemy import Integer, Float, BigInteger, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from datetime import datetime
import uuid


class NodeMetric(BaseModel):
    __tablename__ = "node_metrics"
    __table_args__ = (
        Index("idx_metric_node_time", "node_id", "recorded_at"),
    )

    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    active_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes_total_day: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False
    )
    signal_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    ram_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    node: Mapped["Node"] = relationship("Node", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<NodeMetric id={self.id} node_id={self.node_id} recorded_at={self.recorded_at}>"
