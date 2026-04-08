from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class NodeCreate(BaseModel):
    name: str
    serial: str


class NodeUpdate(BaseModel):
    name: str | None = None


class NodeResponse(BaseModel):
    id: UUID
    name: str
    serial: str
    status: str
    location: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class NodeMetricResponse(BaseModel):
    id: UUID
    node_id: UUID
    recorded_at: datetime
    active_sessions: int
    bytes_total_day: int
    signal_quality: int | None = None
    cpu_percent: float | None = None
    ram_percent: float | None = None

    class Config:
        from_attributes = True
