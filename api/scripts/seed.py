#!/usr/bin/env python3
"""Seed script to create initial test data"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import async_session_maker
from models import User, Tenant, Node, Plan
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    async with async_session_maker() as session:
        # 1. Create superadmin user
        superadmin = User(
            id=uuid4(),
            email="admin@jads.io",
            password_hash=pwd_context.hash("admin123"),
            role="superadmin",
            tenant_id=None,
            is_active=True,
        )
        session.add(superadmin)
        await session.flush()
        print(f"✓ Superadmin creado: admin@jads.io (password: admin123)")

        # 2. Create tenant (operator)
        tenant = Tenant(
            id=uuid4(),
            name="Test Operator",
            slug="test-operator",
            is_active=True,
            plan_tier="starter",
        )
        session.add(tenant)
        await session.flush()
        print(f"✓ Tenant creado: {tenant.name}")

        # 3. Create operator user
        operator = User(
            id=uuid4(),
            email="operator@test.io",
            password_hash=pwd_context.hash("operator123"),
            role="operator",
            tenant_id=tenant.id,
            is_active=True,
        )
        session.add(operator)
        await session.flush()
        print(f"✓ Operator creado: operator@test.io")

        # 4. Create node
        node = Node(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Nodo 01 - Prueba",
            serial="SN001",
            api_key="sk_test_001",
            status="offline",
        )
        session.add(node)
        await session.flush()
        print(f"✓ Nodo creado: {node.name}")

        # 5. Create plans
        plans = [
            Plan(
                id=uuid4(),
                tenant_id=tenant.id,
                name="30 Minutos",
                duration_minutes=30,
                price_usd=Decimal("1.00"),
                bandwidth_down_kbps=0,
                bandwidth_up_kbps=0,
            ),
            Plan(
                id=uuid4(),
                tenant_id=tenant.id,
                name="1 Hora",
                duration_minutes=60,
                price_usd=Decimal("2.00"),
                bandwidth_down_kbps=0,
                bandwidth_up_kbps=0,
            ),
            Plan(
                id=uuid4(),
                tenant_id=tenant.id,
                name="Día Completo",
                duration_minutes=1440,
                price_usd=Decimal("5.00"),
                bandwidth_down_kbps=0,
                bandwidth_up_kbps=0,
            ),
        ]
        for plan in plans:
            session.add(plan)
        await session.flush()
        print(f"✓ {len(plans)} planes creados")

        await session.commit()
        print("\n✅ Seed completado exitosamente")


if __name__ == "__main__":
    asyncio.run(seed())
