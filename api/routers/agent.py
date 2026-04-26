from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from decimal import Decimal

from models.node import Node, NodeStatus
from models.ticket import Ticket, TicketStatus
from models.session import Session as SessionModel
from models.node_metric import NodeMetric
from database import get_db
from deps import get_node_by_api_key

router = APIRouter()


# Request schemas
class MetricsPayload(BaseModel):
    active_sessions: int
    bytes_total_day: int
    signal_quality: int | None = None
    cpu_percent: float | None = None
    ram_percent: float | None = None


class HeartbeatRequest(BaseModel):
    node_id: UUID
    metrics: MetricsPayload


class OfflineActivation(BaseModel):
    code: str
    device_mac: str
    activated_at: datetime


# Response schemas
class HeartbeatResponse(BaseModel):
    ok: bool


class TicketSyncResponse(BaseModel):
    code: str
    status: str
    duration_minutes: int
    plan_id: UUID
    node_id: UUID
    bandwidth_down_kbps: int
    bandwidth_up_kbps: int


class SessionReportResponse(BaseModel):
    processed: int
    failed: int


class AgentConfigResponse(BaseModel):
    node_id: UUID
    node_name: str
    heartbeat_interval: int  # seconds
    sync_interval: int  # seconds
    portal_url: str
    tenant_name: str
    tenant_logo_url: str | None
    tenant_primary_color: str | None


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def agent_heartbeat(
    req: HeartbeatRequest,
    request: Request,
    node: Node = Depends(get_node_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Agent heartbeat: update node status and record metrics.
    Protegido con X-Node-Key header.
    Detecta y almacena la IP WAN del nodo.
    """
    # Verify node_id matches
    if node.id != req.node_id:
        raise HTTPException(status_code=403, detail="Node ID mismatch")

    # Get client IP (this is the WAN IP of the node)
    client_ip = request.client.host if request.client else None

    # Update node
    node.last_seen_at = datetime.now(timezone.utc)
    node.status = NodeStatus.online
    if client_ip:
        node.wan_ip = client_ip

    # Record metric
    metric = NodeMetric(
        node_id=node.id,
        recorded_at=datetime.now(timezone.utc),
        active_sessions=req.metrics.active_sessions,
        bytes_total_day=req.metrics.bytes_total_day,
        signal_quality=req.metrics.signal_quality,
        cpu_percent=req.metrics.cpu_percent,
        ram_percent=req.metrics.ram_percent,
    )

    db.add(metric)
    await db.commit()

    return HeartbeatResponse(ok=True)


@router.get("/tickets/sync", response_model=list[TicketSyncResponse])
async def sync_tickets(
    node_id: UUID,
    node: Node = Depends(get_node_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Return pending and active tickets for the node.
    Agent caches these locally.
    Protegido con X-Node-Key header.
    """
    if node.id != node_id:
        raise HTTPException(status_code=403, detail="Node ID mismatch")

    # Get tickets in pending or active status
    result = await db.execute(
        select(Ticket)
        .join(Ticket.plan)
        .where(
            Ticket.node_id == node_id,
            Ticket.status.in_([TicketStatus.pending, TicketStatus.active]),
        )
    )
    tickets = result.scalars().all()

    return [
        TicketSyncResponse(
            code=t.code,
            status=t.status.value,
            duration_minutes=t.plan.duration_minutes,
            plan_id=t.plan_id,
            node_id=t.node_id,
            bandwidth_down_kbps=t.plan.bandwidth_down_kbps,
            bandwidth_up_kbps=t.plan.bandwidth_up_kbps,
        )
        for t in tickets
    ]


@router.post("/sessions/report", response_model=SessionReportResponse)
async def report_sessions(
    activations: list[OfflineActivation],
    node: Node = Depends(get_node_by_api_key),
    db: AsyncSession = Depends(get_db),
) -> SessionReportResponse:
    """
    Agent reports activations made while offline.
    Idempotent: if session already exists, skips it.
    Protegido con X-Node-Key header.
    """
    processed = 0
    failed = 0

    for activation in activations:
        try:
            # Find ticket
            result = await db.execute(
                select(Ticket).where(
                    Ticket.code == activation.code,
                    Ticket.node_id == node.id,
                )
            )
            ticket = result.scalar_one_or_none()

            if not ticket:
                failed += 1
                continue

            # Skip if already active/expired
            if ticket.status not in [TicketStatus.pending, TicketStatus.active]:
                failed += 1
                continue

            # Check if session already exists
            session_result = await db.execute(
                select(SessionModel).where(SessionModel.ticket_id == ticket.id)
            )
            if session_result.scalar_one_or_none():
                processed += 1
                continue

            # Mark ticket as active
            ticket.status = TicketStatus.active
            ticket.activated_at = activation.activated_at
            ticket.device_mac = activation.device_mac

            # Create session
            expires_at = activation.activated_at + timedelta(
                minutes=ticket.plan.duration_minutes
            )
            session = SessionModel(
                ticket_id=ticket.id,
                node_id=node.id,
                device_mac=activation.device_mac,
                started_at=activation.activated_at,
                expires_at=expires_at,
            )

            db.add(session)
            processed += 1

        except Exception:
            failed += 1

    await db.commit()
    return SessionReportResponse(processed=processed, failed=failed)


@router.get("/config", response_model=AgentConfigResponse)
async def get_agent_config(
    node: Node = Depends(get_node_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Get agent configuration from server.
    Allows dynamic updates without restarting agent.
    Protegido con X-Node-Key header.
    """
    # Load tenant with relationship
    await db.refresh(node, ["tenant"])

    return AgentConfigResponse(
        node_id=node.id,
        node_name=node.name,
        heartbeat_interval=30,  # seconds
        sync_interval=300,  # 5 minutes
        portal_url=f"http://{node.tenant.custom_domain or 'portal.jadslink.io'}",
        tenant_name=node.tenant.name,
        tenant_logo_url=node.tenant.logo_url,
        tenant_primary_color=node.tenant.primary_color
    )
