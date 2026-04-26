from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.session import Session
from models.ticket import Ticket
from models.node import Node
from models.plan import Plan
from database import get_db
from models.user import User
from deps import get_current_user

router = APIRouter()


@router.get("")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active sessions (filtered by tenant for operators, all for superadmin)"""
    from sqlalchemy.orm import selectinload

    query = select(Session).options(
        selectinload(Session.ticket).selectinload(Ticket.plan),
        selectinload(Session.node)
    )

    # Filter by tenant if operator, show all if superadmin
    if current_user.role == "operator" and current_user.tenant_id:
        query = query.join(Ticket).where(
            Ticket.tenant_id == current_user.tenant_id,
            Session.is_active == True,
        )
    elif current_user.role == "superadmin":
        query = query.where(Session.is_active == True)
    else:
        return []

    result = await db.execute(query)
    sessions = result.scalars().unique().all()

    # Enrich with related data
    response = []
    for session in sessions:
        ticket = session.ticket
        node = session.node
        plan = ticket.plan

        response.append({
            "id": str(session.id),
            "ticket_code": ticket.code,
            "mac_address": session.device_mac,
            "status": "active" if session.is_active else "inactive",
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": None,
            "duration_minutes": (session.expires_at - session.started_at).total_seconds() / 60 if session.expires_at and session.started_at else 0,
            "node": {
                "id": str(node.id),
                "name": node.name,
            },
            "plan": {
                "id": str(plan.id),
                "name": plan.name,
                "duration_minutes": plan.duration_minutes,
            },
        })

    return response
