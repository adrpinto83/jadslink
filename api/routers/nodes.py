from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone, timedelta
from models.node import Node
from models.tenant import Tenant
from models.node_metric import NodeMetric
from schemas.node import NodeCreate, NodeUpdate, NodeResponse, NodeMetricResponse
from database import get_db
from deps import get_current_user, get_current_tenant, check_node_limit
import secrets
import asyncio
import json
import logging

log = logging.getLogger("jadslink.nodes")

router = APIRouter()


@router.get("", response_model=list[NodeResponse])
async def list_nodes(
    tenant: Tenant | None = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List nodes.
    - For operators, returns nodes belonging to their tenant.
    - For superadmins, returns all nodes across all tenants.
    """
    query = select(Node)
    if tenant:
        query = query.where(Node.tenant_id == tenant.id)

    result = await db.execute(query.order_by(Node.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_node_limit)])
async def create_node(
    node_in: NodeCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    node = Node(
        tenant_id=tenant.id,
        name=node_in.name,
        serial=node_in.serial,
        api_key=f"sk_live_{secrets.token_hex(16).upper()}",
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: UUID,
    tenant: Tenant | None = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific node.
    - For operators, only returns the node if it belongs to their tenant.
    - For superadmins, returns the node regardless of tenant.
    """
    query = select(Node).where(Node.id == node_id)
    if tenant:
        query = query.where(Node.tenant_id == tenant.id)

    result = await db.execute(query)
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    return node


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: UUID,
    node_in: NodeUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Node).where(
            Node.id == node_id,
            Node.tenant_id == tenant.id,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    if node_in.name:
        node.name = node_in.name

    await db.commit()
    await db.refresh(node)
    return node


@router.get("/{node_id}/metrics", response_model=list[NodeMetricResponse])
async def get_node_metrics(
    node_id: UUID,
    hours: int = 24,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get historical metrics for a node (last N hours)"""
    # Verify node belongs to tenant
    result = await db.execute(
        select(Node).where(
            Node.id == node_id,
            Node.tenant_id == tenant.id,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    # Get metrics from last N hours
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(NodeMetric)
        .where(
            NodeMetric.node_id == node_id,
            NodeMetric.recorded_at >= since,
        )
        .order_by(NodeMetric.recorded_at.desc())
    )
    metrics = result.scalars().all()
    return metrics


@router.get("/{node_id}/stream")
async def stream_node_metrics(
    node_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """SSE stream of node metrics (emitted every 30s)"""
    # Verify node belongs to tenant
    result = await db.execute(
        select(Node).where(
            Node.id == node_id,
            Node.tenant_id == tenant.id,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    async def event_generator():
        """Generate SSE events with node metrics every 30 seconds"""
        try:
            while True:
                # Get latest metric
                async with db.begin_nested():
                    result = await db.execute(
                        select(NodeMetric)
                        .where(NodeMetric.node_id == node_id)
                        .order_by(NodeMetric.recorded_at.desc())
                        .limit(1)
                    )
                    latest_metric = result.scalar_one_or_none()

                # Prepare event data
                event_data = {
                    "status": node.status.value if node.status else "offline",
                    "last_seen_at": node.last_seen_at.isoformat()
                    if node.last_seen_at
                    else None,
                }

                if latest_metric:
                    event_data.update(
                        {
                            "active_sessions": latest_metric.active_sessions,
                            "bytes_total_day": latest_metric.bytes_total_day,
                            "signal_quality": latest_metric.signal_quality,
                            "cpu_percent": latest_metric.cpu_percent,
                            "ram_percent": latest_metric.ram_percent,
                            "recorded_at": latest_metric.recorded_at.isoformat(),
                        }
                    )

                # Emit SSE event
                yield f"data: {json.dumps(event_data)}\n\n"

                # Wait 30 seconds before next event
                await asyncio.sleep(30)

        except asyncio.CancelledError:
            log.debug(f"SSE stream cancelled for node {node_id}")
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
