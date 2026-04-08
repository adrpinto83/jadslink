from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from models.session import Session
from models.ticket import Ticket, TicketStatus
import logging

log = logging.getLogger("jadslink.session_service")


async def expire_sessions(db: AsyncSession) -> int:
    """
    Expire all sessions past their expiration time.
    Marks Session.is_active=False and sets Ticket.status=expired.
    Returns count of sessions expired.
    """
    now = datetime.now(timezone.utc)

    # Find expired active sessions
    result = await db.execute(
        select(Session)
        .where(
            Session.is_active == True,
            Session.expires_at <= now,
        )
        .options(selectinload(Session.ticket))
    )
    sessions = result.scalars().all()

    if not sessions:
        return 0

    # Mark sessions as inactive and tickets as expired
    for session in sessions:
        session.is_active = False
        if session.ticket:
            session.ticket.status = TicketStatus.expired

    await db.commit()

    count = len(sessions)
    log.info(f"Expired {count} session(s)")
    return count
