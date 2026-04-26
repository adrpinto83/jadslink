from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone, timedelta
from models.node import Node
from models.tenant import Tenant
from models.user import User
from models.node_metric import NodeMetric
from schemas.node import NodeCreate, NodeUpdate, NodeResponse, NodeMetricResponse
from database import get_db
from deps import get_current_user, get_current_tenant, check_node_limit
from utils.geolocation import get_location_from_ip
import secrets
import asyncio
import json
import logging

log = logging.getLogger("jadslink.nodes")

router = APIRouter()


@router.get("", response_model=list[NodeResponse])
async def list_nodes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List nodes.
    - For operators, returns nodes belonging to their tenant.
    - For superadmins, returns all nodes across all tenants.
    """
    query = select(Node).where(Node.deleted_at == None)
    if current_user.role != "superadmin":
        if not current_user.tenant_id:
            return [] # Or raise an exception
        query = query.where(Node.tenant_id == current_user.tenant_id)

    result = await db.execute(query.order_by(Node.created_at.desc()))
    return result.scalars().all()


@router.get("/location", tags=["Geolocation"])
async def get_user_location(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Get the current user's location based on their IP address.
    Uses free ip-api.com service (no API key required).
    """
    # Get client IP address
    client_ip = request.client.host if request.client else None

    if not client_ip:
        raise HTTPException(status_code=400, detail="Could not determine client IP address")

    # Get location from IP
    location = await get_location_from_ip(client_ip)

    if not location:
        raise HTTPException(
            status_code=503,
            detail="Geolocation service temporarily unavailable"
        )

    return {
        "ip": client_ip,
        "location": location,
    }


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_node_limit)])
async def create_node(
    node_in: NodeCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    if not tenant:
        raise HTTPException(status_code=403, detail="No active tenant found for user")
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific node.
    - For operators, only returns the node if it belongs to their tenant.
    - For superadmins, returns the node regardless of tenant.
    """
    query = select(Node).where(Node.id == node_id, Node.deleted_at == None)
    if current_user.role != "superadmin":
        if not current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Usuario no asociado a un tenant")
        query = query.where(Node.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    return node


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: UUID,
    node_in: NodeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Node).where(Node.id == node_id, Node.deleted_at == None)
    if current_user.role != "superadmin":
        query = query.where(Node.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    update_data = node_in.model_dump(exclude_unset=True)

    if 'name' in update_data:
        node.name = update_data['name']

    if 'config' in update_data and update_data['config'] is not None:
        if node.config is None:
            node.config = {}
        # Get non-None values from the input config
        config_update = {k: v for k, v in update_data['config'].items() if v is not None}
        node.config.update(config_update)

    if 'location' in update_data and update_data['location'] is not None:
        if node.location is None:
            node.location = {}
        # Get non-None values from the input location
        location_update = {k: v for k, v in update_data['location'].items() if v is not None}
        node.location.update(location_update)

    await db.commit()
    await db.refresh(node)
    return node


@router.post("/{node_id}/detect-location", response_model=NodeResponse)
async def detect_node_location(
    node_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Detect the node's location based on its WAN IP address.
    Uses the WAN IP reported by the node's agent (stored when agent sends heartbeat).
    Updates the node's location automatically using geolocation service.
    """
    # Get the node
    query = select(Node).where(Node.id == node_id, Node.deleted_at == None)
    if current_user.role != "superadmin":
        query = query.where(Node.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    # Use the stored WAN IP from the node (reported via heartbeat)
    # If not available, fallback to current request IP (for newly created nodes)
    node_ip = node.wan_ip or (request.client.host if request.client else None)

    if not node_ip:
        raise HTTPException(status_code=400, detail="No se pudo determinar la IP WAN del nodo. Asegúrate de que el nodo esté conectado y haya reportado su ubicación.")

    # Get geolocation for this IP
    location = await get_location_from_ip(node_ip)

    if not location:
        raise HTTPException(
            status_code=503,
            detail="Servicio de geolocalización no disponible"
        )

    # Update node with detected location
    # Note: We need to reassign the entire location dict for SQLAlchemy to detect the change
    new_location = node.location.copy() if node.location else {}
    new_location.update({
        "lat": location["lat"],
        "lng": location["lng"],
        "address": location["address"],
        "description": f"Auto-detectado: {location['city']}, {location['country']}"
    })

    node.location = new_location

    await db.commit()
    await db.refresh(node)

    log.info(f"Node {node.id} ({node_ip}) location auto-detected: {location['address']}")

    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a node (soft delete by setting deleted_at).
    - For operators, only deletes the node if it belongs to their tenant.
    - For superadmins, can delete any node.
    """
    query = select(Node).where(Node.id == node_id, Node.deleted_at == None)
    if current_user.role != "superadmin":
        if not current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Usuario no asociado a un tenant")
        query = query.where(Node.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    # Soft delete: set deleted_at timestamp
    node.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    return None


@router.get("/{node_id}/metrics", response_model=list[NodeMetricResponse])
async def get_node_metrics(
    node_id: UUID,
    hours: int = 24,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get historical metrics for a node (last N hours)"""
    if not tenant:
        raise HTTPException(status_code=403, detail="No active tenant found for user")
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE stream of node metrics (emitted every 30s)"""
    # Verify node access
    query = select(Node).where(Node.id == node_id)
    if current_user.role != "superadmin":
        query = query.where(Node.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado o sin acceso")

    async def event_generator():
        """Generate SSE events with node metrics every 30 seconds"""
        try:
            while True:
                # Get latest metric
                result = await db.execute(
                    select(NodeMetric)
                    .where(NodeMetric.node_id == node_id)
                    .order_by(NodeMetric.recorded_at.desc())
                    .limit(1)
                )
                latest_metric = result.scalar_one_or_none()

                # Prepare event data
                event_data = {
                    "status": node.status if node.status else "offline",
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
                sse_event = f"""data: {json.dumps(event_data)}

"""
                yield sse_event

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
