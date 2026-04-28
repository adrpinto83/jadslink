
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import func
from uuid import UUID
from datetime import datetime, timezone, timedelta
from pathlib import Path
import aiofiles
import imghdr

from database import get_db
from config import get_settings
from models.tenant import Tenant, PlanTier
from models.node import Node
from models.ticket import Ticket
from models.session import Session as SessionModel
from models.plan import Plan
from models.user import User, UserRole, TenantRole
from schemas.tenant import TenantResponse, TenantUpdate
from schemas.user import (
    UserCreateRequest, UserUpdate, UserResponse, TeamMemberResponse,
    EmployeeListResponse, InviteUserRequest, ChangeRoleRequest, RemoveUserRequest
)
from deps import get_current_tenant, get_current_user, NODE_LIMITS, TICKET_LIMITS
import logging

log = logging.getLogger("jadslink.tenants")

router = APIRouter()
settings = get_settings()

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


@router.get("/me/usage")
async def get_tenant_usage(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get current resource usage (nodes and tickets) for the tenant."""

    # Count active (non-deleted) nodes
    node_result = await db.execute(
        select(func.count(Node.id)).where(
            Node.tenant_id == current_tenant.id,
            Node.deleted_at == None
        )
    )
    nodes_used = node_result.scalar_one()

    # Count tickets from last 30 days
    since = datetime.now(timezone.utc) - timedelta(days=30)
    ticket_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.tenant_id == current_tenant.id,
            Ticket.created_at >= since
        )
    )
    tickets_used = ticket_result.scalar_one()

    # Get plan limits
    nodes_limit = NODE_LIMITS.get(current_tenant.plan_tier, 0)
    tickets_limit = TICKET_LIMITS.get(current_tenant.plan_tier, 0)

    return {
        "plan_tier": current_tenant.plan_tier,
        "subscription_status": current_tenant.subscription_status,
        "nodes": {
            "used": nodes_used,
            "limit": nodes_limit if nodes_limit != -1 else 999999,
            "unlimited": nodes_limit == -1,
        },
        "tickets": {
            "used": tickets_used,
            "limit": tickets_limit if tickets_limit != -1 else 999999,
            "unlimited": tickets_limit == -1,
        },
    }


@router.get("/me/analytics")
async def get_tenant_analytics(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics data for the current tenant (real data, not mock)."""

    # Get last 7 days of ticket creation data
    days_ago_7 = datetime.now(timezone.utc) - timedelta(days=7)

    ticket_result = await db.execute(
        select(
            func.date(Ticket.created_at).label('date'),
            func.count(Ticket.id).label('count')
        )
        .where(
            Ticket.tenant_id == current_tenant.id,
            Ticket.created_at >= days_ago_7
        )
        .group_by(func.date(Ticket.created_at))
        .order_by(func.date(Ticket.created_at))
    )
    tickets_by_day_raw = ticket_result.all()
    tickets_by_day = [
        {
            "date": str(row[0]).split('-')[1:3] if row[0] else '00/00',
            "count": row[1] or 0
        }
        for row in tickets_by_day_raw
    ]
    # Ensure we have 7 days
    if not tickets_by_day:
        tickets_by_day = [
            {
                "date": (datetime.now(timezone.utc) - timedelta(days=6-i)).strftime('%m/%d'),
                "count": 0
            }
            for i in range(7)
        ]

    # Get sessions by plan
    session_result = await db.execute(
        select(
            Plan.name.label('plan'),
            func.count(SessionModel.id).label('count')
        )
        .join(SessionModel.ticket)
        .join(Ticket.plan)
        .where(
            Ticket.tenant_id == current_tenant.id
        )
        .group_by(Plan.name)
        .order_by(func.count(SessionModel.id).desc())
    )
    sessions_by_plan = [
        {"plan": row[0], "count": row[1] or 0}
        for row in session_result.all()
    ]
    if not sessions_by_plan:
        sessions_by_plan = []

    # Get nodes status
    node_result = await db.execute(
        select(
            Node.status.label('status'),
            func.count(Node.id).label('count')
        )
        .where(
            Node.tenant_id == current_tenant.id,
            Node.deleted_at == None
        )
        .group_by(Node.status)
    )
    nodes_status = [
        {"status": row[0] or 'unknown', "count": row[1] or 0}
        for row in node_result.all()
    ]

    # Calculate revenue from tickets (price * activated tickets)
    revenue_result = await db.execute(
        select(
            func.sum(Plan.price_usd).label('total_revenue')
        )
        .join(Ticket.plan)
        .where(
            Ticket.tenant_id == current_tenant.id
        )
    )
    total_revenue = revenue_result.scalar() or 0.0

    return {
        "tickets_by_day": tickets_by_day,
        "sessions_by_plan": sessions_by_plan,
        "nodes_status": nodes_status,
        "total_revenue": float(total_revenue),
        "total_sessions": sum(s["count"] for s in sessions_by_plan),
        "total_nodes": sum(n["count"] for n in nodes_status),
    }  # Fixed: removed SessionModel.tenant_id check, using Ticket.tenant_id instead


@router.post("/me/logo")
async def upload_tenant_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Upload company logo. Only available for tenants with paid plans (Basic or Pro).
    """
    # Check if tenant has paid plan
    if current_tenant.plan_tier == PlanTier.free:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Logo upload solo disponible en planes pagados (Basic o Pro)"
        )

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

    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads/logos")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename based on tenant ID and extension
    file_extension = imghdr.what(None, h=content)
    filename = f"{current_tenant.id}.{file_extension}"
    file_path = uploads_dir / filename

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Update tenant logo URL with absolute path to API server
    if current_tenant.settings is None:
        current_tenant.settings = {}

    # Use absolute URL that points to the API server
    current_tenant.settings["logo_url"] = f"{settings.API_BASE_URL}/uploads/logos/{filename}"
    flag_modified(current_tenant, "settings")

    db.add(current_tenant)
    await db.commit()
    await db.refresh(current_tenant)

    return {
        "status": "success",
        "message": "Logo actualizado exitosamente",
        "logo_url": current_tenant.settings.get("logo_url")
    }


@router.get("/public/logo/{slug}")
async def get_tenant_logo_public(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get tenant logo by slug (public endpoint, no authentication required).
    Used for displaying logo in login/register pages.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.slug == slug)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "logo_url": tenant.settings.get("logo_url") if tenant.settings else None,
    }


# ============================================================================
# GESTIÓN DE EMPLEADOS/COLABORADORES
# ============================================================================

@router.get("/me/employees", response_model=EmployeeListResponse)
async def list_tenant_employees(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Listar todos los empleados/colaboradores del tenant actual.
    """
    if not current_tenant:
        raise HTTPException(status_code=403, detail="No tenant found")

    # Obtener todos los usuarios del tenant
    result = await db.execute(
        select(User).where(User.tenant_id == current_tenant.id).order_by(User.created_at.desc())
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


@router.post("/me/employees", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def invite_employee(
    invite: InviteUserRequest,
    current_tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Invitar a un nuevo empleado/colaborador al tenant.
    Solo owner/admin pueden invitar.
    """
    if not current_tenant:
        raise HTTPException(status_code=403, detail="No tenant found")

    # Validar permisos: solo owner y admin pueden invitar
    if current_user.tenant_role not in [TenantRole.owner, TenantRole.admin]:
        raise HTTPException(
            status_code=403,
            detail="Solo owner y admin pueden invitar empleados"
        )

    # Verificar si el usuario ya existe
    result = await db.execute(select(User).where(User.email == invite.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.tenant_id == current_tenant.id:
            raise HTTPException(
                status_code=409,
                detail="Este usuario ya es miembro del tenant"
            )
        else:
            raise HTTPException(
                status_code=409,
                detail="Este email ya está registrado en otra cuenta"
            )

    # Crear nuevo usuario
    new_user = User(
        email=invite.email,
        full_name=invite.full_name or invite.email.split("@")[0],
        password_hash="",  # Sin contraseña inicial (invitación pendiente)
        role=UserRole.operator,
        tenant_role=invite.tenant_role,
        tenant_id=current_tenant.id,
        is_active=False,  # Desactivado hasta que acepte la invitación
    )

    db.add(new_user)
    await db.flush()
    await db.commit()
    await db.refresh(new_user)

    log.info(f"Employee invited: {new_user.email} to tenant {current_tenant.id}")

    # TODO: Enviar email de invitación con link de activación
    # await EmailService.send_employee_invitation(invite.email, current_tenant.name, ...)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role.value,
        tenant_role=new_user.tenant_role.value if new_user.tenant_role else None,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
    )


@router.patch("/me/employees/{user_id}", response_model=UserResponse)
async def update_employee(
    user_id: UUID,
    update: ChangeRoleRequest,
    current_tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cambiar rol de un empleado.
    Solo owner/admin pueden cambiar roles.
    """
    if not current_tenant:
        raise HTTPException(status_code=403, detail="No tenant found")

    # Validar permisos
    if current_user.tenant_role not in [TenantRole.owner, TenantRole.admin]:
        raise HTTPException(
            status_code=403,
            detail="Solo owner y admin pueden cambiar roles"
        )

    # Obtener usuario
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == current_tenant.id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # No permitir cambiar rol del owner (a menos que sea el owner mismo)
    if user.tenant_role == TenantRole.owner and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="No se puede cambiar el rol del owner"
        )

    # Actualizar rol
    old_role = user.tenant_role.value if user.tenant_role else None
    user.tenant_role = update.tenant_role

    await db.commit()
    await db.refresh(user)

    log.info(f"Employee {user.email} role changed from {old_role} to {update.tenant_role.value}")

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


@router.delete("/me/employees/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_employee(
    user_id: UUID,
    current_tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remover un empleado del tenant (soft delete / desactivar).
    Solo owner/admin pueden remover.
    """
    if not current_tenant:
        raise HTTPException(status_code=403, detail="No tenant found")

    # Validar permisos
    if current_user.tenant_role not in [TenantRole.owner, TenantRole.admin]:
        raise HTTPException(
            status_code=403,
            detail="Solo owner y admin pueden remover empleados"
        )

    # Obtener usuario
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == current_tenant.id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar que no se intente remover al owner
    if user.tenant_role == TenantRole.owner:
        raise HTTPException(
            status_code=403,
            detail="No se puede remover al owner del tenant"
        )

    # Desactivar usuario (soft delete)
    user.is_active = False
    await db.commit()

    log.info(f"Employee removed: {user.email} from tenant {current_tenant.id}")

    return None
