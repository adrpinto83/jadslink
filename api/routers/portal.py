from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone, timedelta
from pathlib import Path
from models.ticket import Ticket, TicketStatus
from models.plan import Plan
from models.node import Node
from models.session import Session as SessionModel
from database import get_db
from services.session_service import SessionService
import logging

log = logging.getLogger("jadslink.portal")

# Path to portal HTML
PORTAL_DIR = Path(__file__).parent.parent / "portal"

router = APIRouter()


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


@router.get("/plans", response_class=HTMLResponse)
async def get_plans_htmx(
    node_id: UUID, # Now required as query param
    db: AsyncSession = Depends(get_db),
):
    """Get available plans for a node and return as HTML options for HTMX."""
    result = await db.execute(
        select(Node).where(Node.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        return "<option value=\"\">No se pudo encontrar el nodo</option>"

    result = await db.execute(
        select(Plan).where(
            Plan.tenant_id == node.tenant_id,
            Plan.is_active,
        ).order_by(Plan.duration_minutes)
    )
    plans = result.scalars().all()

    if not plans:
        return "<option value=\"\">No hay planes disponibles</option>"

    options_html = '<option value=\"\">-- Selecciona un plan --</option>'
    for p in plans:
        options_html += f"<option value=\"{p.id}\" data-price=\"{float(p.price_usd):.2f}\">{p.name} ({p.duration_minutes} min)</option>"

    return options_html

@router.post("/activate", response_class=HTMLResponse)
async def activate_ticket(
    request: Request,
    code: str = Form(...),
    device_mac: str = Form(""), # Default to empty string if not provided
    node_id: UUID = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Activate ticket (public endpoint, no auth) and return HTML partial."""
    # Helper to generate HTML alerts
    def create_alert(message: str, type: str):
        return f"<div class=\"alert alert-{type}\">{message}</div>"

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
                return create_alert("Demasiados intentos de activación. Por favor, espera un momento.", "error")
        except Exception as e:
            log.warning(f"Rate limiting error: {e}")
            # Continue without rate limiting if Redis fails

    # Find ticket with eager load of plan
    result = await db.execute(
        select(Ticket)
        .where(
            Ticket.code == code,
            Ticket.node_id == node_id,
            Ticket.status == TicketStatus.pending,
        )
        .options(selectinload(Ticket.plan))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        return create_alert("Código inválido o ya utilizado.", "error")

    # Use SessionService to activate ticket
    try:
        session_service = SessionService(db)
        session = await session_service.activate_session(
            ticket=ticket,
            node_id=node_id,
            device_mac=device_mac or "00:00:00:00:00:00", # Default MAC if not provided
            user_ip=request.client.host if request.client else None
        )

        minutes_remaining = int((session.expires_at - datetime.now(timezone.utc)).total_seconds() / 60)
        expires_at_str = session.expires_at.astimezone(timezone.utc).strftime("%H:%M:%S UTC")

        return create_alert(
            f"✅ ¡Acceso activado!\n" +
            f"Tienes {minutes_remaining} minutos de conexión.\n" +
            f"Expira: {expires_at_str}",
            "success"
        )

    except HTTPException as e:
        return create_alert(e.detail, "error")
    except Exception as e:
        log.error(f"Error activating session: {e}")
        return create_alert("Ocurrió un error inesperado al activar el acceso.", "error")


@router.get("/status/{code}", response_class=HTMLResponse)
async def ticket_status(
    code: str,
    node_id: UUID | None = None, # Assuming node_id can be passed via hx-get params
    db: AsyncSession = Depends(get_db)
):
    """Check ticket activation status (public endpoint) and return HTML partial."""
    # Helper to generate HTML alerts
    def create_alert(message: str, type: str):
        return f"<div class=\"alert alert-{type}\">{message}</div>"

    query = select(Ticket).where(Ticket.code == code)
    if node_id:
        query = query.where(Ticket.node_id == node_id)

    result = await db.execute(query.options(selectinload(Ticket.plan)))
    ticket = result.scalar_one_or_none()

    if not ticket:
        return create_alert("Ticket no encontrado.", "info")

    if ticket.status == TicketStatus.active and ticket.expires_at:
        now = datetime.now(timezone.utc)
        if now < ticket.expires_at:
            remaining = ticket.expires_at - now
            minutes_remaining = int(remaining.total_seconds() / 60)
            expires_at_str = ticket.expires_at.astimezone(timezone.utc).strftime("%H:%M:%S UTC")
            return create_alert(
                f"✅ Tu acceso está activo. \n" +
                f"Quedan {minutes_remaining} minutos.\n" +
                f"Expira: {expires_at_str}",
                "success"
            )
        else:
            # Ticket expired but status is still active in DB (will be cleaned by APScheduler)
            return create_alert("Tu ticket ha expirado.", "info")
    elif ticket.status == TicketStatus.pending:
        return create_alert("Tu ticket está pendiente de activación.", "info")
    elif ticket.status == TicketStatus.revoked:
        return create_alert("Tu ticket ha sido revocado.", "error")
    elif ticket.status == TicketStatus.expired:
        return create_alert("Tu ticket ha expirado.", "info")
    
    return create_alert("Estado del ticket desconocido.", "info")
