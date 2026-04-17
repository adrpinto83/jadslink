from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TicketGenerateRequest(BaseModel):
    node_id: UUID
    plan_id: UUID
    quantity: int = 1


class TicketResponse(BaseModel):
    id: UUID
    code: str
    qr_data: str
    qr_base64_png: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
