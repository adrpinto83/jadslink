"""
Schemas para endpoints de administración (superadmin).
"""
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class TenantStatsResponse(BaseModel):
    """Estadísticas de un tenant específico."""
    tenant_id: UUID
    tenant_name: str
    tenant_slug: str
    plan_tier: str
    is_active: bool
    subscription_status: str

    nodes_total: int
    nodes_online: int
    nodes_offline: int
    nodes_degraded: int

    tickets_total: int
    tickets_pending: int
    tickets_active: int
    tickets_expired: int
    tickets_revoked: int

    sessions_active: int
    revenue_estimate: float

    class Config:
        from_attributes = True


class PlanCount(BaseModel):
    """Conteo de tenants por plan."""
    plan: str
    count: int


class NodeStatus(BaseModel):
    """Conteo de nodos por estado."""
    status: str
    count: int


class GlobalStatsResponse(BaseModel):
    """Estadísticas globales de toda la plataforma."""
    total_tenants: int
    active_tenants: int
    inactive_tenants: int

    total_nodes: int
    online_nodes: int
    offline_nodes: int
    degraded_nodes: int

    total_tickets: int
    pending_tickets: int
    active_tickets: int
    expired_tickets: int
    revoked_tickets: int

    active_sessions: int
    total_revenue_estimate: float

    tenants_by_plan: list[PlanCount]
    nodes_by_status: list[NodeStatus]

    class Config:
        from_attributes = True


class TenantDetailResponse(BaseModel):
    """Tenant con datos completos para admin."""
    id: UUID
    name: str
    slug: str
    plan_tier: str
    subscription_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Agregados
    nodes_count: int
    tickets_count: int
    sessions_count: int
    users_count: int

    class Config:
        from_attributes = True


class NodeAdminResponse(BaseModel):
    """Nodo con información básica para admin."""
    id: UUID
    name: str
    serial: str
    status: str
    last_seen_at: Optional[datetime]
    location: Optional[dict]
    wan_ip: Optional[str]

    class Config:
        from_attributes = True


class TicketAdminResponse(BaseModel):
    """Ticket con información completa para admin."""
    id: UUID
    code: str
    status: str
    created_at: datetime
    activated_at: Optional[datetime]
    expires_at: Optional[datetime]
    plan_name: Optional[str] = None
    node_name: Optional[str] = None
    device_mac: Optional[str] = None

    class Config:
        from_attributes = True


class SessionAdminResponse(BaseModel):
    """Sesión con información completa para admin."""
    id: UUID
    ticket_id: UUID
    device_mac: str
    ip_address: Optional[str]
    started_at: datetime
    expires_at: datetime
    is_active: bool
    bytes_down: int
    bytes_up: int
    node_name: Optional[str] = None

    class Config:
        from_attributes = True


class TicketsListResponse(BaseModel):
    """Respuesta paginada de tickets."""
    tickets: list[TicketAdminResponse]
    total: int
    page: int
    pages: int

    class Config:
        from_attributes = True
