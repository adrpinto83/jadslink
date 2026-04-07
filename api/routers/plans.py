from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from models.plan import Plan
from models.tenant import Tenant
from schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from database import get_db
from deps import get_current_tenant

router = APIRouter()


@router.get("", response_model=list[PlanResponse])
async def list_plans(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Plan).where(Plan.tenant_id == tenant.id, Plan.is_active)
    )
    return result.scalars().all()


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_in: PlanCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    plan = Plan(
        tenant_id=tenant.id,
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
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Plan).where(
            Plan.id == plan_id,
            Plan.tenant_id == tenant.id,
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    if plan_in.name:
        plan.name = plan_in.name
    if plan_in.price_usd:
        plan.price_usd = plan_in.price_usd

    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Plan).where(
            Plan.id == plan_id,
            Plan.tenant_id == tenant.id,
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    plan.is_active = False
    await db.commit()
