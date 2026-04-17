import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.session_service import SessionService
from models.ticket import Ticket, TicketStatus
from models.session import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_activate_session_success(db_session: AsyncSession, setup_data):
    """Test successful session activation."""
    session_service = SessionService(db_session)
    ticket = setup_data["ticket"]
    node = setup_data["node"]
    device_mac = "AA:BB:CC:DD:EE:FF"

    session = await session_service.activate_session(ticket, node.id, device_mac, "127.0.0.1")

    assert session is not None
    assert session.ticket_id == ticket.id
    assert session.node_id == node.id
    assert session.device_mac == device_mac
    assert session.is_active is True
    assert ticket.status == TicketStatus.active
    assert ticket.activated_at is not None
    assert ticket.expires_at is not None
    assert ticket.device_mac == device_mac

    expected_expires_at = ticket.activated_at + timedelta(minutes=setup_data["plan"].duration_minutes)
    assert abs((ticket.expires_at - expected_expires_at).total_seconds()) < 1


@pytest.mark.asyncio
async def test_activate_session_ticket_already_active(db_session: AsyncSession, setup_data):
    """Test that activating an already active ticket raises exception."""
    session_service = SessionService(db_session)
    ticket = setup_data["ticket"]
    node = setup_data["node"]

    # Activate once
    await session_service.activate_session(ticket, node.id, "AA:BB:CC:DD:EE:FF", "127.0.0.1")

    # Try to activate again
    with pytest.raises(HTTPException) as exc_info:
        await session_service.activate_session(ticket, node.id, "BB:CC:DD:EE:FF:11", "127.0.0.1")

    assert exc_info.value.status_code == 400
    assert "no está pendiente" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_expire_sessions_expired_session(db_session: AsyncSession, setup_data):
    """Test expiring sessions that have passed their expiration time."""
    session_service = SessionService(db_session)
    ticket = setup_data["ticket"]
    node = setup_data["node"]

    # Create an active session
    session = await session_service.activate_session(ticket, node.id, "AA:BB:CC:DD:EE:FF", "127.0.0.1")

    # Manually set expiration to past
    session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    ticket.expires_at = session.expires_at
    await db_session.commit()

    # Run expire job
    expired_count = await session_service.expire_sessions()

    assert expired_count == 1

    # Verify session is inactive
    await db_session.refresh(session)
    await db_session.refresh(ticket)
    assert session.is_active is False
    assert ticket.status == TicketStatus.expired


@pytest.mark.asyncio
async def test_expire_sessions_no_expired_sessions(db_session: AsyncSession, setup_data):
    """Test expire_sessions when no sessions are expired."""
    session_service = SessionService(db_session)
    ticket = setup_data["ticket"]
    node = setup_data["node"]

    # Create an active session with future expiration
    await session_service.activate_session(ticket, node.id, "AA:BB:CC:DD:EE:FF", "127.0.0.1")

    # Run expire job
    expired_count = await session_service.expire_sessions()

    assert expired_count == 0


@pytest.mark.asyncio
async def test_activate_session_stores_ip_address(db_session: AsyncSession, setup_data):
    """Test that session stores the user's IP address."""
    session_service = SessionService(db_session)
    ticket = setup_data["ticket"]
    node = setup_data["node"]
    test_ip = "192.168.1.100"

    session = await session_service.activate_session(ticket, node.id, "AA:BB:CC:DD:EE:FF", test_ip)

    assert session.ip_address == test_ip
