from __future__ import annotations
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from jose import JWTError, jwt
from config import get_settings
from database import get_db
from uuid import UUID
from datetime import datetime, timezone, timedelta

# Import models for internal logic, not for top-level type hints
from models.user import User
from models.tenant import Tenant
from models.node import Node
from models.ticket import Ticket


settings = get_settings()
security = HTTPBearer()

# Plan limits: nodes
NODE_LIMITS = {
    "starter": 1,
    "pro": 5,
    "enterprise": -1,  # Unlimited
}

# Plan limits: tickets per month
TICKET_LIMITS = {
    "starter": 50,
    "pro": 500,
    "enterprise": -1,  # Unlimited
}

# Backward compatibility
PLAN_LIMITS = NODE_LIMITS

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> "User":
    """Extract and verify JWT token, return current user"""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o inválido",
        )

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    return user


async def get_current_tenant(
    current_user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> "Tenant":
    """
    Get current user's tenant. Raises 403 if user has no tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no asociado a un tenant",
        )

    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        # This case should ideally not happen if data is consistent
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant no encontrado para el usuario {current_user.id}",
        )
    return tenant


async def get_node_by_api_key(
    x_node_key: str = Header(..., alias="X-Node-Key"),
    db: AsyncSession = Depends(get_db),
) -> "Node":
    """Authenticate a field agent by node API key from X-Node-Key header"""
    result = await db.execute(select(Node).where(Node.api_key == x_node_key))
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida",
        )
    return node

async def check_node_limit(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Dependency to enforce node limits based on the tenant's plan."""
    if not tenant:
        return

    limit = NODE_LIMITS.get(tenant.plan_tier, 0)
    if limit == -1:
        return

    count_result = await db.execute(
        select(func.count(Node.id)).where(
            Node.tenant_id == tenant.id,
            Node.deleted_at == None
        )
    )
    node_count = count_result.scalar_one()

    if node_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Límite de nodos ({limit}) alcanzado para el plan '{tenant.plan_tier}'. Upgrade requerido."
        )

async def check_ticket_limit(
    quantity: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Dependency to enforce ticket generation limits based on the tenant's plan."""
    if not tenant:
        return

    limit = TICKET_LIMITS.get(tenant.plan_tier, 0)
    if limit == -1:
        return

    since = datetime.now(timezone.utc) - timedelta(days=30)
    count_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.tenant_id == tenant.id,
            Ticket.created_at >= since
        )
    )
    ticket_count = count_result.scalar_one()
    remaining = limit - ticket_count

    if ticket_count + quantity > limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Límite de {limit} tickets/mes excedido. Disponibles: {remaining}. Upgrade requerido."
        )


def get_superadmin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is a superadmin."""
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de superadministrador."
        )
    return current_user
