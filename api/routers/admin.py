from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from uuid import UUID
from pathlib import Path
import aiofiles
import imghdr
import logging
from datetime import datetime, timedelta
import math

from database import get_db
from config import get_settings
from models.tenant import Tenant, PlanTier
from models.user import User, UserRole, TenantRole
from models.node import Node, NodeStatus
from models.ticket import Ticket, TicketStatus
from models.session import Session
from models.plan import Plan
from schemas.tenant import TenantResponse, GrantFreeSubscriptionRequest, SubscriptionInfo
from schemas.user import (
    UserResponse, TeamMemberResponse, EmployeeListResponse,
    ChangeRoleRequest, RemoveUserRequest
)
from schemas.admin import (
    GlobalStatsResponse, TenantStatsResponse, TenantDetailResponse,
    NodeAdminResponse, TicketAdminResponse, SessionAdminResponse,
    TicketsListResponse, PlanCount, NodeStatus as NodeStatusSchema
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


# ============================================================================
# PANEL DE GESTIÓN DE TENANTS - ESTADÍSTICAS Y RECURSOS
# ============================================================================

@router.get("/overview", response_model=GlobalStatsResponse)
async def admin_global_overview(
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Obtiene estadísticas globales de toda la plataforma para superadmin.
    Incluye conteos de tenants, nodos, tickets y sesiones.
    """
    # Total de tenants
    tenants_result = await db.execute(select(func.count()).select_from(Tenant))
    total_tenants = tenants_result.scalar() or 0

    active_tenants_result = await db.execute(
        select(func.count()).select_from(Tenant).where(Tenant.is_active == True)
    )
    active_tenants = active_tenants_result.scalar() or 0
    inactive_tenants = total_tenants - active_tenants

    # Total de nodos por estado
    nodes_result = await db.execute(select(func.count()).select_from(Node))
    total_nodes = nodes_result.scalar() or 0

    online_nodes_result = await db.execute(
        select(func.count()).select_from(Node).where(Node.status == NodeStatus.online)
    )
    online_nodes = online_nodes_result.scalar() or 0

    offline_nodes_result = await db.execute(
        select(func.count()).select_from(Node).where(Node.status == NodeStatus.offline)
    )
    offline_nodes = offline_nodes_result.scalar() or 0

    degraded_nodes_result = await db.execute(
        select(func.count()).select_from(Node).where(Node.status == NodeStatus.degraded)
    )
    degraded_nodes = degraded_nodes_result.scalar() or 0

    # Total de tickets por estado
    tickets_result = await db.execute(select(func.count()).select_from(Ticket))
    total_tickets = tickets_result.scalar() or 0

    pending_tickets_result = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.status == TicketStatus.pending)
    )
    pending_tickets = pending_tickets_result.scalar() or 0

    active_tickets_result = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.status == TicketStatus.active)
    )
    active_tickets = active_tickets_result.scalar() or 0

    expired_tickets_result = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.status == TicketStatus.expired)
    )
    expired_tickets = expired_tickets_result.scalar() or 0

    revoked_tickets_result = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.status == TicketStatus.revoked)
    )
    revoked_tickets = revoked_tickets_result.scalar() or 0

    # Sesiones activas
    active_sessions_result = await db.execute(
        select(func.count()).select_from(Session).where(Session.is_active == True)
    )
    active_sessions = active_sessions_result.scalar() or 0

    # Tenants por plan
    tenants_by_plan_result = await db.execute(
        select(Tenant.plan_tier, func.count()).select_from(Tenant).group_by(Tenant.plan_tier)
    )
    tenants_by_plan = [
        PlanCount(plan=plan.value, count=count)
        for plan, count in tenants_by_plan_result
    ]

    # Nodos por estado
    nodes_by_status_result = await db.execute(
        select(Node.status, func.count()).select_from(Node).group_by(Node.status)
    )
    nodes_by_status = [
        NodeStatusSchema(status=status.value, count=count)
        for status, count in nodes_by_status_result
    ]

    # Estimar ingresos (tickets activos * precio promedio)
    # Suponemos un precio promedio de $2.50 por ticket
    avg_ticket_price = 2.50
    total_revenue_estimate = active_tickets * avg_ticket_price

    return GlobalStatsResponse(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        inactive_tenants=inactive_tenants,
        total_nodes=total_nodes,
        online_nodes=online_nodes,
        offline_nodes=offline_nodes,
        degraded_nodes=degraded_nodes,
        total_tickets=total_tickets,
        pending_tickets=pending_tickets,
        active_tickets=active_tickets,
        expired_tickets=expired_tickets,
        revoked_tickets=revoked_tickets,
        active_sessions=active_sessions,
        total_revenue_estimate=total_revenue_estimate,
        tenants_by_plan=tenants_by_plan,
        nodes_by_status=nodes_by_status,
    )


@router.get("/tenants/{tenant_id}/stats", response_model=TenantStatsResponse)
async def admin_tenant_stats(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Obtiene estadísticas completas de un tenant específico.
    """
    # Obtener tenant
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Nodos
    nodes_total_result = await db.execute(
        select(func.count()).select_from(Node).where(Node.tenant_id == tenant_id)
    )
    nodes_total = nodes_total_result.scalar() or 0

    nodes_online_result = await db.execute(
        select(func.count()).select_from(Node).where(
            and_(Node.tenant_id == tenant_id, Node.status == NodeStatus.online)
        )
    )
    nodes_online = nodes_online_result.scalar() or 0

    nodes_offline_result = await db.execute(
        select(func.count()).select_from(Node).where(
            and_(Node.tenant_id == tenant_id, Node.status == NodeStatus.offline)
        )
    )
    nodes_offline = nodes_offline_result.scalar() or 0

    nodes_degraded_result = await db.execute(
        select(func.count()).select_from(Node).where(
            and_(Node.tenant_id == tenant_id, Node.status == NodeStatus.degraded)
        )
    )
    nodes_degraded = nodes_degraded_result.scalar() or 0

    # Tickets
    tickets_total_result = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.tenant_id == tenant_id)
    )
    tickets_total = tickets_total_result.scalar() or 0

    tickets_pending_result = await db.execute(
        select(func.count()).select_from(Ticket).where(
            and_(Ticket.tenant_id == tenant_id, Ticket.status == TicketStatus.pending)
        )
    )
    tickets_pending = tickets_pending_result.scalar() or 0

    tickets_active_result = await db.execute(
        select(func.count()).select_from(Ticket).where(
            and_(Ticket.tenant_id == tenant_id, Ticket.status == TicketStatus.active)
        )
    )
    tickets_active = tickets_active_result.scalar() or 0

    tickets_expired_result = await db.execute(
        select(func.count()).select_from(Ticket).where(
            and_(Ticket.tenant_id == tenant_id, Ticket.status == TicketStatus.expired)
        )
    )
    tickets_expired = tickets_expired_result.scalar() or 0

    tickets_revoked_result = await db.execute(
        select(func.count()).select_from(Ticket).where(
            and_(Ticket.tenant_id == tenant_id, Ticket.status == TicketStatus.revoked)
        )
    )
    tickets_revoked = tickets_revoked_result.scalar() or 0

    # Sesiones activas
    sessions_active_result = await db.execute(
        select(func.count()).select_from(Session).where(
            and_(
                Session.is_active == True,
                Session.node_id.in_(
                    select(Node.id).where(Node.tenant_id == tenant_id)
                )
            )
        )
    )
    sessions_active = sessions_active_result.scalar() or 0

    # Ingresos estimados
    avg_ticket_price = 2.50
    revenue_estimate = tickets_active * avg_ticket_price

    # Manejo de enums
    plan_tier_value = tenant.plan_tier.value if hasattr(tenant.plan_tier, 'value') else str(tenant.plan_tier)
    subscription_status_value = tenant.subscription_status.value if hasattr(tenant.subscription_status, 'value') else str(tenant.subscription_status)

    return TenantStatsResponse(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        tenant_slug=tenant.slug,
        plan_tier=plan_tier_value,
        is_active=tenant.is_active,
        subscription_status=subscription_status_value,
        nodes_total=nodes_total,
        nodes_online=nodes_online,
        nodes_offline=nodes_offline,
        nodes_degraded=nodes_degraded,
        tickets_total=tickets_total,
        tickets_pending=tickets_pending,
        tickets_active=tickets_active,
        tickets_expired=tickets_expired,
        tickets_revoked=tickets_revoked,
        sessions_active=sessions_active,
        revenue_estimate=revenue_estimate,
    )


@router.get("/tenants/{tenant_id}/nodes", response_model=list[NodeAdminResponse])
async def admin_tenant_nodes(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Obtiene lista de todos los nodos de un tenant específico.
    """
    # Verificar que el tenant existe
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Obtener nodos
    result = await db.execute(
        select(Node).where(Node.tenant_id == tenant_id).order_by(Node.created_at.desc())
    )
    nodes = result.scalars().all()

    return [
        NodeAdminResponse(
            id=node.id,
            name=node.name,
            serial=node.serial,
            status=node.status.value,
            last_seen_at=node.last_seen_at,
            location=node.location,
            wan_ip=node.wan_ip,
        )
        for node in nodes
    ]


@router.get("/tenants/{tenant_id}/tickets", response_model=TicketsListResponse)
async def admin_tenant_tickets(
    tenant_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Obtiene lista paginada de tickets de un tenant específico.
    """
    # Verificar que el tenant existe
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Contar total de tickets
    count_result = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.tenant_id == tenant_id)
    )
    total = count_result.scalar() or 0

    # Obtener tickets paginados
    result = await db.execute(
        select(Ticket)
        .where(Ticket.tenant_id == tenant_id)
        .order_by(Ticket.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tickets = result.scalars().all()

    # Obtener información de planes y nodos para cada ticket
    tickets_data = []
    for ticket in tickets:
        # Obtener plan
        plan = await db.get(Plan, ticket.plan_id)
        plan_name = plan.name if plan else None

        # Obtener nodo
        node = await db.get(Node, ticket.node_id)
        node_name = node.name if node else None

        status_value = ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status)

        tickets_data.append(
            TicketAdminResponse(
                id=ticket.id,
                code=ticket.code,
                status=status_value,
                created_at=ticket.created_at,
                activated_at=ticket.activated_at,
                expires_at=ticket.expires_at,
                plan_name=plan_name,
                node_name=node_name,
                device_mac=ticket.device_mac,
            )
        )

    pages = math.ceil(total / limit) if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1

    return TicketsListResponse(
        tickets=tickets_data,
        total=total,
        page=page,
        pages=pages,
    )


@router.get("/tenants/{tenant_id}/sessions", response_model=list[SessionAdminResponse])
async def admin_tenant_sessions(
    tenant_id: UUID,
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Obtiene lista de sesiones de un tenant específico.
    Opcionalmente filtra solo sesiones activas.
    """
    # Verificar que el tenant existe
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Construir query
    query = select(Session).where(
        Session.node_id.in_(
            select(Node.id).where(Node.tenant_id == tenant_id)
        )
    )

    if active_only:
        query = query.where(Session.is_active == True)

    query = query.order_by(Session.started_at.desc())

    result = await db.execute(query)
    sessions = result.scalars().all()

    # Obtener información de nodos para cada sesión
    sessions_data = []
    for session in sessions:
        node = await db.get(Node, session.node_id)
        node_name = node.name if node else None

        sessions_data.append(
            SessionAdminResponse(
                id=session.id,
                ticket_id=session.ticket_id,
                device_mac=session.device_mac,
                ip_address=session.ip_address,
                started_at=session.started_at,
                expires_at=session.expires_at,
                is_active=session.is_active,
                bytes_down=session.bytes_down,
                bytes_up=session.bytes_up,
                node_name=node_name,
            )
        )

    return sessions_data


@router.patch("/tenants/{tenant_id}/suspend", response_model=TenantResponse)
async def admin_suspend_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Suspende un tenant (is_active = False).
    El tenant ya no puede acceder a la plataforma.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if not tenant.is_active:
        raise HTTPException(status_code=400, detail="Tenant ya está suspendido")

    tenant.is_active = False
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    log.info(f"Admin suspended tenant {tenant.name}")

    return tenant


@router.patch("/tenants/{tenant_id}/activate", response_model=TenantResponse)
async def admin_activate_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Reactiva un tenant suspendido (is_active = True).
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    if tenant.is_active:
        raise HTTPException(status_code=400, detail="Tenant ya está activo")

    tenant.is_active = True
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    log.info(f"Admin activated tenant {tenant.name}")

    return tenant


@router.get("/tenants", response_model=list[TenantDetailResponse])
async def admin_list_tenants_detailed(
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin),
):
    """
    Superadmin lista todos los tenants/operadores con información detallada.
    Incluye conteo de nodos, tickets, sesiones y usuarios.
    """
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = result.scalars().all()

    tenants_data = []
    for tenant in tenants:
        # Contar nodos
        nodes_result = await db.execute(
            select(func.count()).select_from(Node).where(Node.tenant_id == tenant.id)
        )
        nodes_count = nodes_result.scalar() or 0

        # Contar tickets
        tickets_result = await db.execute(
            select(func.count()).select_from(Ticket).where(Ticket.tenant_id == tenant.id)
        )
        tickets_count = tickets_result.scalar() or 0

        # Contar sesiones
        sessions_result = await db.execute(
            select(func.count()).select_from(Session).where(
                Session.node_id.in_(
                    select(Node.id).where(Node.tenant_id == tenant.id)
                )
            )
        )
        sessions_count = sessions_result.scalar() or 0

        # Contar usuarios
        users_result = await db.execute(
            select(func.count()).select_from(User).where(User.tenant_id == tenant.id)
        )
        users_count = users_result.scalar() or 0

        # Manejo de enums
        plan_tier_value = tenant.plan_tier.value if hasattr(tenant.plan_tier, 'value') else str(tenant.plan_tier)
        subscription_status_value = tenant.subscription_status.value if hasattr(tenant.subscription_status, 'value') else str(tenant.subscription_status)

        tenants_data.append(
            TenantDetailResponse(
                id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                plan_tier=plan_tier_value,
                subscription_status=subscription_status_value,
                is_active=tenant.is_active,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at,
                nodes_count=nodes_count,
                tickets_count=tickets_count,
                sessions_count=sessions_count,
                users_count=users_count,
            )
        )

    return tenants_data
