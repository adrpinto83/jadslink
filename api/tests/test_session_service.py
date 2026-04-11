import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from services.session_service import SessionService
from models.ticket import Ticket, TicketStatus
from datetime import timedelta

@pytest.mark.asyncio
async def test_activate_session_success(db_session: AsyncSession, setup_data):
    """Test successful session activation."""
    session_service = SessionService(db_session)
    ticket = setup_data["ticket"]
    node = setup_data["node"]
    device_mac = "AA:BB:CC:DD:EE:FF"

    # Activate the session
    session = await session_service.activate_session(ticket, node.id, device_mac, "127.0.0.1")

    # Assertions
    assert session is not None
    assert session.ticket_id == ticket.id
    assert session.node_id == node.id
    assert session.device_mac == device_mac
    assert ticket.status == TicketStatus.active
    assert ticket.activated_at is not None
    assert ticket.expires_at is not None

    # Verify expiration time is correct
    expected_expires_at = ticket.activated_at + timedelta(minutes=setup_data["plan"].duration_minutes)
    assert abs(ticket.expires_at - expected_expires_at) < timedelta(seconds=1) # Allow for small time differences
