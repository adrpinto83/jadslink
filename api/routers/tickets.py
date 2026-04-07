from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timezone, timedelta
from models.ticket import Ticket
from models.plan import Plan
from models.node import Node
from models.tenant import Tenant
from schemas.ticket import TicketGenerateRequest, TicketResponse
from database import get_db
from deps import get_current_tenant
from services.ticket_service import generate_ticket_code, generate_qr_base64
from config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/generate", response_model=list[TicketResponse], status_code=status.HTTP_201_CREATED)
async def generate_tickets(
    req: TicketGenerateRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    # Verify node belongs to tenant
    result = await db.execute(
        select(Node).where(
            Node.id == req.node_id,
            Node.tenant_id == tenant.id,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    # Verify plan belongs to tenant
    result = await db.execute(
        select(Plan).where(
            Plan.id == req.plan_id,
            Plan.tenant_id == tenant.id,
            Plan.is_active,
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    # Generate tickets
    tickets = []
    for _ in range(req.quantity):
        code = generate_ticket_code(settings.TICKET_HMAC_SECRET)
        qr_url = f"https://jadslink.io/activate?code={code}&node={req.node_id}"
        ticket = Ticket(
            code=code,
            qr_data=qr_url,
            tenant_id=tenant.id,
            node_id=req.node_id,
            plan_id=req.plan_id,
        )
        db.add(ticket)
        tickets.append(ticket)

    await db.commit()
    for ticket in tickets:
        await db.refresh(ticket)

    return tickets


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Ticket).where(Ticket.tenant_id == tenant.id)
    )
    return result.scalars().all()
