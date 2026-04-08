from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from pathlib import Path
from models.ticket import Ticket, TicketStatus
from models.plan import Plan
from models.node import Node
from models.session import Session as SessionModel
from database import get_db
import logging

log = logging.getLogger("jadslink.portal")

# Path to portal HTML
PORTAL_DIR = Path(__file__).parent.parent / "portal"

router = APIRouter()


class ActivateRequest(BaseModel):
    code: str
    device_mac: str
    node_id: UUID


class ActivateResponse(BaseModel):
    ok: bool
    minutes_remaining: int | None = None
    expires_at: str | None = None


@router.get("", response_class=HTMLResponse)
async def portal_page():
    """Serve captive portal HTML"""
    html_file = PORTAL_DIR / "index.html"
    if html_file.exists():
        return html_file.read_text(encoding="utf-8")

    # Fallback if file not found
    log.warning("Portal HTML file not found")
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>JADSlink</title></head>
    <body><h1>Portal not available</h1></body>
    </html>
    """


@router.get("/plans/{node_id}")
async def get_plans(node_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get available plans for a node (public endpoint)"""
    result = await db.execute(
        select(Node).where(Node.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")

    result = await db.execute(
        select(Plan).where(
            Plan.tenant_id == node.tenant_id,
            Plan.is_active,
        )
    )
    plans = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "duration_minutes": p.duration_minutes,
            "price_usd": float(p.price_usd),
        }
        for p in plans
    ]


@router.post("/activate", response_model=ActivateResponse)
async def activate_ticket(
    req: ActivateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Activate ticket (public endpoint, no auth)"""
    # Rate limiting: max 10 attempts per IP per minute
    redis = getattr(request.app.state, "redis", None)
    if redis:
        client_ip = request.client.host if request.client else "unknown"
        rate_limit_key = f"portal:activate:{client_ip}"

        try:
            attempts = await redis.incr(rate_limit_key)
            if attempts == 1:
                await redis.expire(rate_limit_key, 60)  # 60 second window

            if attempts > 10:
                log.warning(f"Rate limit exceeded for IP {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many activation attempts",
                )
        except HTTPException:
            raise
        except Exception as e:
            log.warning(f"Rate limiting error: {e}")
            # Continue without rate limiting if Redis fails

    # Find ticket with eager load of plan
    result = await db.execute(
        select(Ticket)
        .where(
            Ticket.code == req.code,
            Ticket.node_id == req.node_id,
            Ticket.status == TicketStatus.pending,
        )
        .options(selectinload(Ticket.plan))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        return ActivateResponse(ok=False)

    # Mark ticket as active
    ticket.status = TicketStatus.active
    ticket.activated_at = datetime.now(timezone.utc)
    ticket.device_mac = req.device_mac

    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ticket.plan.duration_minutes
    )
    ticket.expires_at = expires_at

    session = SessionModel(
        ticket_id=ticket.id,
        node_id=req.node_id,
        device_mac=req.device_mac,
        started_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()

    minutes_remaining = ticket.plan.duration_minutes
    return ActivateResponse(
        ok=True,
        minutes_remaining=minutes_remaining,
        expires_at=expires_at.isoformat(),
    )


@router.get("/status/{code}")
async def ticket_status(code: str, db: AsyncSession = Depends(get_db)):
    """Check ticket activation status (public endpoint)"""
    result = await db.execute(
        select(Ticket).where(Ticket.code == code)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        return {
            "ok": False,
            "is_active": False,
            "minutes_remaining": None,
        }

    if ticket.status != TicketStatus.active:
        return {
            "ok": False,
            "is_active": False,
            "minutes_remaining": None,
        }

    # Calculate remaining time
    if ticket.expires_at:
        now = datetime.now(timezone.utc)
        remaining = ticket.expires_at - now
        minutes_remaining = max(0, int(remaining.total_seconds() / 60))
    else:
        minutes_remaining = None

    return {
        "ok": True,
        "is_active": True,
        "minutes_remaining": minutes_remaining,
    }
