from __future__ import annotations
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from jose import JWTError, jwt
from config import get_settings
from database import get_db
from uuid import UUID

# Import models for internal logic, not for top-level type hints
from models.user import User
from models.tenant import Tenant
from models.node import Node


settings = get_settings()
security = HTTPBearer()

# Plan limits
PLAN_LIMITS = {
    "starter": 5,
    "pro": 50,
    "enterprise": -1,  # Unlimited
}

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
    if not tenant: # This happens for superadmin
        return

    limit = PLAN_LIMITS.get(tenant.plan_tier, 0)
    if limit == -1:  # Unlimited
        return

    count_result = await db.execute(
        select(func.count(Node.id)).where(Node.tenant_id == tenant.id)
    )
    node_count = count_result.scalar_one()

    if node_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Límite de nodos ({limit}) para el plan '{tenant.plan_tier}' alcanzado."
        )
