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
