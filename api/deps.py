from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from config import get_settings
from database import get_db
from uuid import UUID


settings = get_settings()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
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

    from models.user import User

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
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's tenant, or raise if superadmin"""
    from models.tenant import Tenant

    if current_user.role == "superadmin":
        # Superadmin tiene tenant_id = None, no retorna un tenant específico
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endpoint no disponible para superadmin",
        )

    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant no encontrado",
        )
    return tenant


async def get_node_by_api_key(
    api_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate a field agent by node API key"""
    from models.node import Node

    result = await db.execute(select(Node).where(Node.api_key == api_key))
    node = result.scalar_one_or_none()
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida",
        )
    return node
