
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified
from uuid import UUID

from database import get_db
from models.tenant import Tenant
from schemas.tenant import TenantResponse, TenantUpdate
from deps import get_current_tenant

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
