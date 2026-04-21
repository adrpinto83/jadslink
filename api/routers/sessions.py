from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.session import Session
from database import get_db
from models.user import User
from deps import get_current_user

router = APIRouter()


@router.get("")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active sessions for the current tenant"""
    if not current_user.tenant_id:
        return []

    query = select(Session).where(
        Session.tenant_id == current_user.tenant_id,
        Session.status == "active",
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    return [
        {
            "id": str(session.id),
            "ticket_id": str(session.ticket_id),
            "node_id": str(session.node_id),
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "user_ip": session.user_ip,
            "user_mac": session.user_mac,
            "data_used_mb": session.data_used_mb,
        }
        for session in sessions
    ]
