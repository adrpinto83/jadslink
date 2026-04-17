from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from models.plan import Plan
from models.tenant import Tenant
from schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from database import get_db
from models.user import User
from deps import get_current_user, get_current_tenant

router = APIRouter()


@router.get("", response_model=list[PlanResponse])
async def list_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Superadmin sees all active plans from all tenants
    if current_user.role == "superadmin":
        query = select(Plan).where(Plan.is_active == True)
    else:
        if not current_user.tenant_id:
            return []
        query = select(Plan).where(
            and_(Plan.tenant_id == current_user.tenant_id, Plan.is_active == True)
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_in: PlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Regular operators can only create plans for their own tenant.
    # Superadmins, for now, also create plans for their own primary tenant.
    # This simplifies the UI as they don't need to select a tenant.
    if not current_user.tenant_id:
        raise HTTPException(status_code=403, detail="User is not associated with a tenant.")

    plan = Plan(
        tenant_id=current_user.tenant_id,
        name=plan_in.name,
        duration_minutes=plan_in.duration_minutes,
        price_usd=plan_in.price_usd,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: UUID,
    plan_in: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Plan).where(Plan.id == plan_id)
    # Regular users can only update plans within their own tenant
    if current_user.role != "superadmin":
        query = query.where(Plan.tenant_id == current_user.tenant_id)
    
    result = await db.execute(query)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or you do not have permission")

    update_data = plan_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Plan).where(Plan.id == plan_id)
    # Regular users can only delete plans within their own tenant
    if current_user.role != "superadmin":
        query = query.where(Plan.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or you do not have permission")
    
    plan.is_active = False
    await db.commit()
