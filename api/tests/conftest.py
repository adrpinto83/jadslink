import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.ticket import Ticket, TicketStatus
from models.plan import Plan
from models.node import Node
from models.tenant import Tenant
from datetime import datetime, timedelta, timezone
import uuid

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Create a new database session with an in-memory SQLite database."""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback() # Rollback any changes after the test

@pytest.fixture
async def setup_data(db_session: AsyncSession):
    """Set up initial data for tests."""
    # Create a tenant
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant", slug="test-tenant")
    db_session.add(tenant)
    await db_session.flush()

    # Create a node
    node = Node(id=uuid.uuid4(), tenant_id=tenant.id, name="Test Node", serial="12345", api_key="test_api_key")
    db_session.add(node)
    await db_session.flush()

    # Create a plan
    plan = Plan(id=uuid.uuid4(), tenant_id=tenant.id, name="Test Plan", duration_minutes=30, price_usd=1.0)
    db_session.add(plan)
    await db_session.flush()

    # Create a ticket
    ticket = Ticket(
        id=uuid.uuid4(), 
        code="TEST1234", 
        qr_data="test_qr_data",
        tenant_id=tenant.id, 
        node_id=node.id, 
        plan_id=plan.id, 
        status=TicketStatus.pending
    )
    db_session.add(ticket)
    await db_session.commit()

    return {
        "tenant": tenant,
        "node": node,
        "plan": plan,
        "ticket": ticket
    }
