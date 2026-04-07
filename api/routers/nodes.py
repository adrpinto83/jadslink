from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from models.node import Node
from models.tenant import Tenant
from schemas.node import NodeCreate, NodeUpdate, NodeResponse
from database import get_db
from deps import get_current_user, get_current_tenant
import secrets

router = APIRouter()


@router.get("", response_model=list[NodeResponse])
async def list_nodes(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Node).where(Node.tenant_id == tenant.id)
    )
    return result.scalars().all()


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
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
