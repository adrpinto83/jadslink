from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from models.session import Session
from models.ticket import Ticket, TicketStatus
import logging

log = logging.getLogger("jadslink.session_service")


class SessionService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def expire_sessions(self) -> int:
        """
        Expire all sessions past their expiration time.
        Marks Session.is_active=False and sets Ticket.status=expired.
        Returns count of sessions expired.
        """
        now = datetime.now(timezone.utc)

        # Find expired active sessions
        result = await self.db.execute(
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

        await self.db.commit()

        count = len(sessions)
        log.info(f"Expired {count} session(s)")
        return count

    async def activate_session(self, ticket: Ticket, node_id: str, device_mac: str, user_ip: str) -> Session:
        """Activate a ticket and create a new session."""
        if ticket.status != TicketStatus.pending:
            raise HTTPException(
                status_code=400,
                detail="El ticket no está pendiente de activación",
            )

        ticket.status = TicketStatus.active
        ticket.activated_at = datetime.now(timezone.utc)
        ticket.device_mac = device_mac

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=ticket.plan.duration_minutes
        )
        ticket.expires_at = expires_at

        session = Session(
            ticket_id=ticket.id,
            node_id=node_id,
            device_mac=device_mac,
            ip_address=user_ip,
            started_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        log.info(f"Ticket {ticket.code} activado para {device_mac} en nodo {node_id}")
        return session
