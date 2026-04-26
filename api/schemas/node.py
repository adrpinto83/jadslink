from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class NodeLocation(BaseModel):
    lat: float | None = None
    lng: float | None = None
    address: str | None = None
    description: str | None = None


class NodeConfigUpdate(BaseModel):
    # WiFi Configuration
    ssid: str | None = None
    channel: int | None = None
    max_clients: int | None = None
    bandwidth_default: int | None = None
    # Router Communication
    api_endpoint: str | None = None
    heartbeat_interval: int | None = None  # seconds
    metrics_interval: int | None = None    # seconds
    enable_metrics: bool | None = None


class NodeCreate(BaseModel):
    name: str
    serial: str
    config: NodeConfigUpdate | None = None


class NodeUpdate(BaseModel):
    name: str | None = None
    config: NodeConfigUpdate | None = None
    location: NodeLocation | None = None


class NodeResponse(BaseModel):
    id: UUID
    name: str
    serial: str
    status: str
    location: NodeLocation | None = None
    config: NodeConfigUpdate | None = None
    last_seen_at: datetime | None = None
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
