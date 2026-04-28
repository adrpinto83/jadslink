from __future__ import annotations
from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
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
security = HTTPBearer(auto_error=False)  # Don't auto-error, we'll handle missing credentials manually

# Plan definitions with new pricing model
"""
PLAN TIERS:
- free: Gratuito para demostración
  * 1 nodo máximo
  * 50 tickets gratis incluidos
  * Soporte por email

- basic: Pago por uso (Pay-as-you-go)
  * 1 nodo máximo
  * $0.50 por cada 50 tickets generados (después de los 50 gratis iniciales)
  * Soporte prioritario

- pro: Plan empresarial
  * Nodos ilimitados
  * Tickets ilimitados
  * API pública
  * Soporte 24/7
  * Planes personalizados
"""

# Plan limits: nodes
NODE_LIMITS = {
    "free": 1,        # 1 node máximo
    "basic": 1,       # 1 node máximo
    "pro": -1,        # Unlimited
}

# Plan limits: tickets per month
# For free and basic: limited to 50 free tickets per month
# For pro: unlimited
TICKET_LIMITS = {
    "free": 50,       # 50 free tickets per month
    "basic": 50,      # After 50 free, charges $0.50 per 50 tickets
    "pro": -1,        # Unlimited tickets
}

# Backward compatibility
PLAN_LIMITS = NODE_LIMITS

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> "User":
    """Extract and verify JWT token, return current user

    Supports multiple token sources (in order of priority):
    1. Authorization: Bearer <token> header (standard)
    2. X-Authorization header (for proxy compatibility)
    3. Authorization query parameter (for debugging)
    4. Access token cookie (for SPA compatibility)
    """
    token = None

    # Try standard Authorization header first (with HTTPBearer)
    if credentials:
        token = credentials.credentials

    # If no token from HTTPBearer, try alternative sources
    if not token and request:
        # Try X-Authorization header (for proxy compatibility)
        token = request.headers.get("X-Authorization", "").replace("Bearer ", "")

        # Try Authorization query parameter
        if not token:
            token = request.query_params.get("access_token", "")

        # Try cookie
        if not token:
            token = request.cookies.get("access_token", "")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
        )

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

    # Import here to avoid circular imports
    from services.limits_service import LimitsService

    can_create, message = await LimitsService.can_create_node(tenant, db)
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=message
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

    # For free and basic plans: enforce the free tier limit (50 tickets)
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
        if tenant.plan_tier == "free":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Límite de {limit} tickets/mes alcanzado en el plan Gratuito. Upgrade a Básico o Pro para continuar."
            )
        elif tenant.plan_tier == "basic":
            # For basic plan: after 50 free tickets, charge $0.50 per 50 tickets
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Límite de {limit} tickets gratis/mes alcanzado en el plan Básico. Cada 50 tickets adicionales cuesta $0.50. Contacta a soporte para habilitar cobro automático o upgrade a Pro."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Límite de {limit} tickets/mes alcanzado. Upgrade requerido."
            )


async def get_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure current user is a superadmin.
    Raises 403 if user is not a superadmin.
    """
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo superadmin puede acceder a este recurso",
        )
    return current_user
