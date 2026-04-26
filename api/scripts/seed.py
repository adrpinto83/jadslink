#!/usr/bin/env python3
"""Seed script to create initial test data"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from database import async_session_maker
from models import User, Tenant, Node, Plan
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    async with async_session_maker() as session:
        async with session.begin():
            # 1. Create JADS Studio tenant for the superadmin
            result = await session.execute(select(Tenant).where(Tenant.slug == "jads-studio"))
            jads_tenant = result.scalar_one_or_none()
            if not jads_tenant:
                jads_tenant = Tenant(
                    id=uuid4(),
                    name="JADS Studio",
                    slug="jads-studio",
                    is_active=True,
                    plan_tier="pro", # The main company has the highest tier
                )
                session.add(jads_tenant)
                print(f"✓ Tenant creado: {jads_tenant.name}")
            else:
                print(f"✓ Tenant ya existe: {jads_tenant.name}")

            # 2. Create superadmin user
            result = await session.execute(select(User).where(User.email == "admin@jads.com"))
            superadmin = result.scalar_one_or_none()
            if not superadmin:
                superadmin = User(
                    id=uuid4(),
                    email="admin@jads.com",
                    password_hash=pwd_context.hash("admin123456"),
                    role="superadmin",
                    tenant_id=jads_tenant.id, # Associate with JADS tenant
                    is_active=True,
                )
                session.add(superadmin)
                print("✓ Superadmin creado: admin@jads.com (password: admin123456)")
            else:
                # Ensure existing superadmin is associated with the JADS tenant
                if not superadmin.tenant_id:
                    superadmin.tenant_id = jads_tenant.id
                    print("✓ Superadmin actualizado con tenant_id de JADS Studio")
                print("✓ Superadmin ya existe")

            # 3. Create tenant (operator) with Free plan
            result = await session.execute(select(Tenant).where(Tenant.slug == "test-operator"))
            tenant = result.scalar_one_or_none()
            if not tenant:
                tenant = Tenant(
                    id=uuid4(),
                    name="Test Operator",
                    slug="test-operator",
                    is_active=True,
                    plan_tier="free",
                    subscription_status="trialing",
                    free_tickets_limit=50,
                    free_tickets_used=0,
                )
                session.add(tenant)
                print(f"✓ Tenant creado: {tenant.name} (Plan Free - 50 tickets de demostración)")
            else:
                print(f"✓ Tenant ya existe: {tenant.name}")

            # 3. Create operator user
            result = await session.execute(select(User).where(User.email == "operator@test.com"))
            operator = result.scalar_one_or_none()
            if not operator:
                operator = User(
                    id=uuid4(),
                    email="operator@test.com",
                    password_hash=pwd_context.hash("operator123456"),
                    role="operator",
                    tenant_id=tenant.id,
                    is_active=True,
                )
                session.add(operator)
                print("✓ Operator creado: operator@test.com (password: operator123456)")
            else:
                print("✓ Operator ya existe")


            # 4. Create node
            result = await session.execute(select(Node).where(Node.serial == "SN001"))
            node = result.scalar_one_or_none()
            if not node:
                node = Node(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    name="Nodo 01 - Prueba",
                    serial="SN001",
                    api_key="sk_test_001",
                    status="offline",
                )
                session.add(node)
                print(f"✓ Nodo creado: {node.name}")
            else:
                print(f"✓ Nodo ya existe: {node.name}")


            # 5. Create plans
            plan_definitions = [
                {
                    "name": "30 Minutos",
                    "duration_minutes": 30,
                    "price_usd": Decimal("1.00"),
                },
                {
                    "name": "1 Hora",
                    "duration_minutes": 60,
                    "price_usd": Decimal("2.00"),
                },
                {
                    "name": "Día Completo",
                    "duration_minutes": 1440,
                    "price_usd": Decimal("5.00"),
                },
            ]

            for plan_def in plan_definitions:
                result = await session.execute(select(Plan).where(Plan.name == plan_def["name"], Plan.tenant_id == tenant.id))
                plan = result.scalars().first()
                if not plan:
                    plan = Plan(
                        id=uuid4(),
                        tenant_id=tenant.id,
                        name=plan_def["name"],
                        duration_minutes=plan_def["duration_minutes"],
                        price_usd=plan_def["price_usd"],
                        bandwidth_down_kbps=0,
                        bandwidth_up_kbps=0,
                    )
                    session.add(plan)
                    print(f"✓ Plan creado: {plan.name}")
                else:
                    print(f"✓ Plan ya existe: {plan.name}")

            await session.commit()
            print("✅ Seed completado exitosamente")


if __name__ == "__main__":
    asyncio.run(seed())
