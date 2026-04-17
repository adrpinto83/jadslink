from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from models.ticket import Ticket
from models.plan import Plan
from models.node import Node
from models.user import User
from schemas.ticket import TicketGenerateRequest, TicketResponse
from database import get_db
from deps import get_current_user
from services.ticket_service import generate_ticket_code, generate_qr_base64
from config import get_settings

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

    await db.commit()

    response_tickets = []
    for ticket in db_tickets:
        await db.refresh(ticket)
        qr_base64 = generate_qr_base64(ticket.qr_data)
        response_tickets.append(
            TicketResponse(
                id=ticket.id,
                code=ticket.code,
                qr_data=ticket.qr_data,
                qr_base64_png=qr_base64,
                status=ticket.status.value, # Correctly use the enum's value
                created_at=ticket.created_at,
            )
        )

    return response_tickets


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == "superadmin":
        query = select(Ticket)
    else:
        if not current_user.tenant_id:
            return []
        query = select(Ticket).where(Ticket.tenant_id == current_user.tenant_id)

    result = await db.execute(query)
    return result.scalars().all()
