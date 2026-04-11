from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from database import get_db
from models.tenant import Tenant
from schemas.tenant import TenantResponse
from deps import get_current_user
from models.user import User
from services.subscription_service import create_stripe_customer

router = APIRouter()

def get_superadmin(current_user: User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de superadministrador."
        )
    return current_user


@router.patch("/tenants/{tenant_id}/approve", response_model=TenantResponse)
async def approve_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin)
):
    """Approve a tenant, setting them to active."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    if tenant.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ya está activo")

    tenant.is_active = True
    await create_stripe_customer(tenant, db) # Create Stripe customer
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return tenant
