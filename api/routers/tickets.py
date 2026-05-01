from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from uuid import UUID
from datetime import datetime, timezone, timedelta
from models.ticket import Ticket
from models.plan import Plan
from models.node import Node
from models.tenant import Tenant
from models.user import User
from schemas.ticket import TicketGenerateRequest, TicketResponse
from database import get_db
from deps import get_current_user, TICKET_LIMITS
from services.ticket_service import generate_ticket_code, generate_qr_base64
from services.limits_service import LimitsService
from config import get_settings
from schemas.ticket import BatchRevokeRequest

router = APIRouter()
settings = get_settings()


@router.post("/generate", response_model=list[TicketResponse], status_code=status.HTTP_201_CREATED)
async def generate_tickets(
    req: TicketGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify node and get tenant_id from it
    node_result = await db.execute(select(Node).where(Node.id == req.node_id))
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    tenant_id = node.tenant_id

    # If user is not superadmin, check if they have access to this tenant
    if current_user.role != "superadmin" and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para este nodo")

    # Get tenant settings
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Check ticket limits using the new service
    can_generate, limit_message = await LimitsService.can_generate_tickets(
        tenant, req.quantity, db
    )
    if not can_generate:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=limit_message
        )

    # Verify plan belongs to the same tenant
    plan_result = await db.execute(
        select(Plan).where(
            Plan.id == req.plan_id,
            Plan.tenant_id == tenant_id,
            Plan.is_active,
        )
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado en el tenant del nodo")

    # Generate tickets
    db_tickets = []
    for _ in range(req.quantity):
        code = generate_ticket_code(settings.TICKET_HMAC_SECRET)
        qr_url = f"https://jadslink.io/activate?code={code}&node={req.node_id}"
        ticket = Ticket(
            code=code,
            qr_data=qr_url,
            tenant_id=tenant_id,
            node_id=req.node_id,
            plan_id=req.plan_id,
        )
        db.add(ticket)
        db_tickets.append(ticket)

    # Record ticket generation and update tenant limits
    usage_info = await LimitsService.record_ticket_generation(tenant, req.quantity, db)

    await db.commit()

    response_tickets = []
    # No need to refresh tickets - all data is already in memory after commit()
    for ticket in db_tickets:
        qr_base64 = generate_qr_base64(ticket.qr_data)
        response_tickets.append(
            TicketResponse(
                id=ticket.id,
                code=ticket.code,
                qr_data=ticket.qr_data,
                qr_base64_png=qr_base64,
                status=ticket.status.value,
                created_at=ticket.created_at,
                plan_name=plan.name,
                tenant_logo_url=tenant.settings.get("logo_url"),
                tenant_ssid=tenant.settings.get("ssid"),
            )
        )

    return response_tickets


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_deleted: bool = False,
):
    # Use eager loading instead of manual JOINs for better SQLAlchemy patterns
    query = select(Ticket).options(
        joinedload(Ticket.plan),
        joinedload(Ticket.tenant)
    )

    if current_user.role != "superadmin":
        if not current_user.tenant_id:
            return []
        query = query.where(Ticket.tenant_id == current_user.tenant_id)

    # Filter deleted by default
    if not include_deleted:
        query = query.where(Ticket.deleted_at == None)

    result = await db.execute(query)

    # Use unique() to handle potential duplicates from multiple joinedloads
    tickets = result.unique().scalars().all()

    response_tickets = []
    for ticket in tickets:
        qr_base64 = generate_qr_base64(ticket.qr_data)
        response_tickets.append(
            TicketResponse(
                id=ticket.id,
                code=ticket.code,
                qr_data=ticket.qr_data,
                qr_base64_png=qr_base64,
                status=ticket.status.value,
                created_at=ticket.created_at,
                plan_name=ticket.plan.name,
                tenant_logo_url=ticket.tenant.settings.get("logo_url"),
                tenant_ssid=ticket.tenant.settings.get("ssid"),
            )
        )

    return response_tickets


@router.post("/{ticket_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke_ticket(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke a ticket (change status to revoked).
    Only pending or active tickets can be revoked.
    """
    query = select(Ticket).where(Ticket.id == ticket_id)

    # Filter by tenant if not superadmin
    if current_user.role != "superadmin":
        if not current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Usuario no asociado a un tenant")
        query = query.where(Ticket.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # Check if ticket can be revoked
    if ticket.status.value not in ['pending', 'active']:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede revocar un ticket con estado '{ticket.status.value}'"
        )

    # Revoke the ticket
    from models.ticket import TicketStatus
    ticket.status = TicketStatus.revoked
    await db.commit()

    return {"message": "Ticket revocado exitosamente", "ticket_id": str(ticket.id)}


@router.post("/revoke-multiple", status_code=status.HTTP_200_OK)
async def revoke_multiple_tickets(
    req: BatchRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.ticket_ids:
        raise HTTPException(status_code=400, detail="No se proporcionaron IDs de tickets")

    query = select(Ticket).where(Ticket.id.in_(req.ticket_ids))

    if current_user.role != "superadmin":
        if not current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Usuario no asociado a un tenant")
        query = query.where(Ticket.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    tickets_to_revoke = result.scalars().all()

    if len(tickets_to_revoke) != len(req.ticket_ids):
        raise HTTPException(status_code=404, detail="Algunos tickets no se encontraron o no pertenecen a tu tenant")

    revoked_count = 0
    for ticket in tickets_to_revoke:
        if ticket.status.value in ['pending', 'active']:
            ticket.status = 'revoked'
            revoked_count += 1

    await db.commit()

    return {"message": f"{revoked_count} tickets revocados exitosamente"}


@router.post("/delete-multiple", status_code=status.HTTP_200_OK)
async def delete_multiple_tickets(
    req: BatchRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete multiple tickets from the database.
    """
    if not req.ticket_ids:
        raise HTTPException(status_code=400, detail="No se proporcionaron IDs de tickets")

    query = select(Ticket).where(Ticket.id.in_(req.ticket_ids))

    if current_user.role != "superadmin":
        if not current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Usuario no asociado a un tenant")
        query = query.where(Ticket.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    tickets_to_delete = result.scalars().all()

    if len(tickets_to_delete) != len(req.ticket_ids):
        raise HTTPException(status_code=404, detail="Algunos tickets no se encontraron o no pertenecen a tu tenant")

    deleted_count = len(tickets_to_delete)
    for ticket in tickets_to_delete:
        await db.delete(ticket)

    await db.commit()

    return {"message": f"{deleted_count} tickets eliminados permanentemente"}


@router.delete("/{ticket_id}", status_code=status.HTTP_200_OK)
async def delete_ticket(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a ticket from the database.
    Only the operator who owns the ticket or superadmin can delete.
    """
    query = select(Ticket).where(Ticket.id == ticket_id)

    # Filter by tenant if not superadmin
    if current_user.role != "superadmin":
        if not current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Usuario no asociado a un tenant")
        query = query.where(Ticket.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # Delete the ticket permanently
    await db.delete(ticket)
    await db.commit()

    return {"message": "Ticket eliminado permanentemente", "ticket_id": str(ticket.id)}
