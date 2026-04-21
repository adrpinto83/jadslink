
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import func
from uuid import UUID
from datetime import datetime, timezone, timedelta

from database import get_db
from models.tenant import Tenant
from models.node import Node
from models.ticket import Ticket
from schemas.tenant import TenantResponse, TenantUpdate
from deps import get_current_tenant, NODE_LIMITS, TICKET_LIMITS

router = APIRouter()

@router.get("/me", response_model=TenantResponse)
async def read_tenant_me(current_tenant: Tenant = Depends(get_current_tenant)):
    """
    Get the current tenant's details.
    """
    return current_tenant

@router.patch("/me", response_model=TenantResponse)
async def update_tenant_me(
    tenant_update: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Update the current tenant's settings.
    """
    updated_settings = tenant_update.model_dump(exclude_unset=True)

    if not updated_settings:
        raise HTTPException(status_code=400, detail="No settings to update")

    # Assumes settings is a JSON field
    if current_tenant.settings is None:
        current_tenant.settings = {}

    current_tenant.settings.update(updated_settings)
    flag_modified(current_tenant, "settings")

    db.add(current_tenant)
    await db.commit()
    await db.refresh(current_tenant)

    return current_tenant


@router.get("/me/usage")
async def get_tenant_usage(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get current resource usage (nodes and tickets) for the tenant."""

    # Count active (non-deleted) nodes
    node_result = await db.execute(
        select(func.count(Node.id)).where(
            Node.tenant_id == current_tenant.id,
            Node.deleted_at == None
        )
    )
    nodes_used = node_result.scalar_one()

    # Count tickets from last 30 days
    since = datetime.now(timezone.utc) - timedelta(days=30)
    ticket_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.tenant_id == current_tenant.id,
            Ticket.created_at >= since
        )
    )
    tickets_used = ticket_result.scalar_one()

    # Get plan limits
    nodes_limit = NODE_LIMITS.get(current_tenant.plan_tier, 0)
    tickets_limit = TICKET_LIMITS.get(current_tenant.plan_tier, 0)

    return {
        "plan_tier": current_tenant.plan_tier,
        "subscription_status": current_tenant.subscription_status,
        "nodes": {
            "used": nodes_used,
            "limit": nodes_limit if nodes_limit != -1 else float('inf'),
            "unlimited": nodes_limit == -1,
        },
        "tickets": {
            "used": tickets_used,
            "limit": tickets_limit if tickets_limit != -1 else float('inf'),
            "unlimited": tickets_limit == -1,
        },
    }
