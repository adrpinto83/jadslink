from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from models.ticket import Ticket, TicketStatus
from models.plan import Plan
from models.node import Node
from models.session import Session as SessionModel
from database import get_db

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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>JADSlink - Conectividad Satelital</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, system-ui, sans-serif; background: #f5f5f5; padding: 20px; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2563eb; margin-bottom: 20px; font-size: 24px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; color: #333; font-weight: 500; }
            input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
            button { width: 100%; padding: 12px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; margin-top: 10px; }
            button:hover { background: #1d4ed8; }
            .info { color: #666; font-size: 13px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛰️ JADSlink</h1>
            <p style="color: #666; margin-bottom: 20px;">Conectividad satelital rápida y confiable</p>
            <form hx-post="/api/v1/portal/activate" hx-target="#response">
                <div class="form-group">
                    <label>Código de acceso</label>
                    <input type="text" name="code" placeholder="Ingrese su código" required>
                </div>
                <div class="form-group">
                    <label>Dirección MAC del dispositivo</label>
                    <input type="text" name="device_mac" placeholder="00:00:00:00:00:00" required>
                </div>
                <input type="hidden" name="node_id" value="{node_id}">
                <button type="submit">Activar Acceso</button>
            </form>
            <div id="response"></div>
            <div class="info">
                <p>¿No tienes código? Contacta al operador de la red.</p>
            </div>
        </div>
        <script src="https://unpkg.com/htmx.org"></script>
    </body>
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
    req: ActivateRequest, db: AsyncSession = Depends(get_db)
):
    """Activate ticket (public endpoint, no auth)"""
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
