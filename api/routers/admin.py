from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from pathlib import Path
import aiofiles
import imghdr
import logging
from datetime import datetime, timedelta

from database import get_db
from config import get_settings
from models.tenant import Tenant, PlanTier
from models.user import User, UserRole, TenantRole
from schemas.tenant import TenantResponse, GrantFreeSubscriptionRequest, SubscriptionInfo
from schemas.user import (
    UserResponse, TeamMemberResponse, EmployeeListResponse,
    ChangeRoleRequest, RemoveUserRequest
)
from deps import get_superadmin
from services.subscription_service import create_stripe_customer

log = logging.getLogger("jadslink.admin")

router = APIRouter()
settings = get_settings()


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


@router.post("/logo")
async def upload_app_logo(
    file: UploadFile = File(...),
    superadmin: User = Depends(get_superadmin),
):
    """
    Upload JADSlink application logo (admin only).
    This logo appears in all parts of the app where "JADSlink" appears.
    """
    # Validate file type
    if not file.filename or not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo inválido"
        )

    # Read file content
    content = await file.read()

    # Validate file size (max 5MB)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Archivo demasiado grande (máximo 5MB)"
        )

    # Validate image type
    image_type = imghdr.what(None, h=content)
    if image_type not in ["jpeg", "png", "gif", "webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan imágenes (JPEG, PNG, GIF, WebP)"
        )

    # Create uploads/app directory if it doesn't exist
    uploads_dir = Path("uploads/app")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename for JADSlink logo (fixed name, replaces existing)
    file_extension = imghdr.what(None, h=content)
    filename = f"jadslink.{file_extension}"
    file_path = uploads_dir / filename

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    logo_url = f"{settings.API_PREFIX}/uploads/app/{filename}"

    return {
        "status": "success",
        "message": "Logo de JADSlink actualizado exitosamente",
        "logo_url": logo_url
    }


@router.get("/logo/public")
async def get_app_logo_public():
    """
    Get JADSlink application logo (public endpoint, no authentication required).
    Used for displaying logo in login/register and throughout the app.
    Returns relative URL so it works in both dev and production.
    """
    # Check if logo exists
    uploads_dir = Path("uploads/app")
    logo_files = list(uploads_dir.glob("jadslink.*"))

    if logo_files:
        # Logo exists, return its relative URL
        logo_filename = logo_files[0].name
        # Return relative URL that will be resolved relative to the current API
        logo_url = f"{settings.API_PREFIX}/uploads/app/{logo_filename}"
        return {
            "logo_url": logo_url,
            "has_custom_logo": True
        }
    else:
        # No custom logo, return null
        return {
            "logo_url": None,
            "has_custom_logo": False
        }


# ============================================================================
# GESTIÓN DE TENANTS POR SUPERADMIN
# ============================================================================

@router.get("/tenants")
async def admin_list_tenants(
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Superadmin lista todos los tenants/operadores.
    """
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()

    return [
        {
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "is_active": tenant.is_active,
        }
        for tenant in tenants
    ]


# ============================================================================
# GESTIÓN DE EMPLEADOS POR SUPERADMIN (para cualquier tenant)
# ============================================================================

@router.get("/tenants/{tenant_id}/employees", response_model=EmployeeListResponse)
async def admin_list_tenant_employees(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Superadmin lista todos los empleados de un tenant específico.
    """
    # Verificar que el tenant existe
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Obtener todos los usuarios del tenant
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    # Contar por rol
    role_counts = {
        "owner": 0,
        "admin": 0,
        "collaborator": 0,
        "viewer": 0,
    }

    for user in users:
        if user.tenant_role:
            role_counts[user.tenant_role.value] += 1

    members = [
        TeamMemberResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            tenant_role=user.tenant_role.value if user.tenant_role else "collaborator",
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]

    return EmployeeListResponse(
        members=members,
        total_count=len(users),
        role_counts=role_counts,
    )


@router.patch("/tenants/{tenant_id}/employees/{user_id}", response_model=UserResponse)
async def admin_change_employee_role(
    tenant_id: UUID,
    user_id: UUID,
    update: ChangeRoleRequest,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Superadmin cambia rol de un empleado en cualquier tenant.
    """
    # Verificar que el tenant existe
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Obtener usuario del tenant
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en este tenant")

    # No permitir cambiar rol del owner
    if user.tenant_role == TenantRole.owner:
        raise HTTPException(
            status_code=403,
            detail="No se puede cambiar el rol del owner"
        )

    # Actualizar rol
    old_role = user.tenant_role.value if user.tenant_role else None
    user.tenant_role = update.tenant_role

    await db.commit()
    await db.refresh(user)

    log.info(f"Admin changed role of {user.email}: {old_role} → {update.tenant_role.value}")

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        tenant_role=user.tenant_role.value if user.tenant_role else None,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete("/tenants/{tenant_id}/employees/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_remove_employee(
    tenant_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Superadmin remueve un empleado de cualquier tenant (soft delete).
    """
    # Verificar que el tenant existe
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Obtener usuario del tenant
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en este tenant")

    # No permitir remover al owner
    if user.tenant_role == TenantRole.owner:
        raise HTTPException(
            status_code=403,
            detail="No se puede remover al owner del tenant"
        )

    # Desactivar usuario
    user.is_active = False
    await db.commit()

    log.info(f"Admin removed employee {user.email} from tenant {tenant.name}")

    return None


# ============================================================================
# GESTIÓN DE SUSCRIPCIONES GRATUITAS POR SUPERADMIN
# ============================================================================

@router.get("/tenants/{tenant_id}/subscription", response_model=SubscriptionInfo)
async def get_tenant_subscription_info(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Superadmin obtiene información de suscripción de un tenant.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Verificar si la suscripción gratuita ya expiró
    is_free_active = False
    if tenant.free_subscription_until:
        is_free_active = datetime.utcnow() < tenant.free_subscription_until

    # Handle both Enum and string values (for compatibility with different DB migrations)
    plan_tier_value = tenant.plan_tier.value if hasattr(tenant.plan_tier, 'value') else str(tenant.plan_tier)
    subscription_status_value = tenant.subscription_status.value if hasattr(tenant.subscription_status, 'value') else str(tenant.subscription_status)

    return SubscriptionInfo(
        plan_tier=plan_tier_value,
        subscription_status=subscription_status_value,
        free_subscription_until=tenant.free_subscription_until,
        free_subscription_plan=tenant.free_subscription_plan,
        free_subscription_reason=tenant.free_subscription_reason,
        is_free_subscription_active=is_free_active,
    )


@router.post("/tenants/{tenant_id}/subscription/grant")
async def grant_free_subscription(
    tenant_id: UUID,
    request: GrantFreeSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Superadmin otorga una suscripción gratuita a un tenant.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Validar plan
    valid_plans = ["pro", "basic"]
    if request.plan not in valid_plans:
        raise HTTPException(
            status_code=400,
            detail=f"Plan inválido. Válidos: {', '.join(valid_plans)}",
        )

    # Calcular fecha de expiración
    free_until = datetime.utcnow() + timedelta(days=request.days)

    # Actualizar tenant
    tenant.plan_tier = PlanTier.pro if request.plan == "pro" else PlanTier.basic
    tenant.free_subscription_until = free_until
    tenant.free_subscription_plan = request.plan
    tenant.free_subscription_reason = request.reason

    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    log.info(
        f"Admin granted free {request.plan} subscription to tenant {tenant.name} for {request.days} days"
    )

    return {
        "status": "success",
        "message": f"Suscripción {request.plan.upper()} gratuita otorgada por {request.days} días",
        "tenant_name": tenant.name,
        "plan": request.plan,
        "expires_at": free_until,
        "reason": request.reason,
    }


@router.post("/tenants/{tenant_id}/subscription/revoke")
async def revoke_free_subscription(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Superadmin revoca una suscripción gratuita de un tenant.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if not tenant.free_subscription_until:
        raise HTTPException(
            status_code=400,
            detail="Este tenant no tiene suscripción gratuita",
        )

    # Revertir a plan free
    tenant.plan_tier = PlanTier.free
    tenant.free_subscription_until = None
    tenant.free_subscription_plan = None
    tenant.free_subscription_reason = None

    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    log.info(f"Admin revoked free subscription from tenant {tenant.name}")

    return {
        "status": "success",
        "message": "Suscripción gratuita revocada. Tenant revertido a plan FREE",
        "tenant_name": tenant.name,
    }
