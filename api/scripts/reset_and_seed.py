#!/usr/bin/env python3
"""
Script para limpiar TODA la base de datos y crear datos demo de prueba.

Crea:
- Cuenta DEMO: demo@jadslink.com / demo123456
  * Con nodos, planes, tickets y sesiones de ejemplo
  * Prefecto para demostración y testing

- Cuenta ADMIN: admin@jads.com / admin123456
  * Superadmin para gestión del sistema
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from database import async_session_maker, engine
from models import User, Tenant, Node, Plan, Ticket, Session as DBSession
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def drop_all_tables():
    """Elimina TODAS las tablas de la base de datos"""
    async with engine.begin() as conn:
        print("🗑️  Limpiando base de datos...")
        await conn.run_sync(lambda c: print("  Eliminando todas las tablas..."))

        # Drop all tables in reverse order of dependencies
        tables_to_drop = [
            "node_metrics",
            "sessions",
            "tickets",
            "plans",
            "nodes",
            "users",
            "tenants",
        ]

        for table in tables_to_drop:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  ✓ Tabla '{table}' eliminada")
            except Exception as e:
                print(f"  ⚠️  Error al eliminar '{table}': {e}")

        await conn.commit()
        print("✅ Base de datos limpia\n")


async def create_all_tables():
    """Crea todas las tablas"""
    from models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tablas creadas\n")


async def seed_demo_data():
    """Crea datos de demostración completos"""
    async with async_session_maker() as session:
        async with session.begin():
            print("📝 Creando datos de demostración...\n")

            # =================================================================
            # 1. CREAR TENANT DEMO (Para la demostración pública)
            # =================================================================
            print("1️⃣  CUENTA DEMO (Demostración Pública)")
            print("-" * 50)

            demo_tenant = Tenant(
                id=uuid4(),
                name="Demo - Bus Starlink",
                slug="demo-bus-starlink",
                is_active=True,
                plan_tier="free",
                subscription_status="active",
                free_tickets_limit=50,
                free_tickets_used=0,
            )
            session.add(demo_tenant)
            print(f"✓ Tenant creado: {demo_tenant.name}")

            # Usuario demo
            demo_user = User(
                id=uuid4(),
                email="demo@jadslink.com",
                password_hash=pwd_context.hash("demo123456"),
                role="operator",
                tenant_id=demo_tenant.id,
                is_active=True,
            )
            session.add(demo_user)
            print("✓ Usuario creado: demo@jadslink.com (password: demo123456)")

            # Planes para cuenta demo
            demo_plans = [
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
                {
                    "name": "Semanal",
                    "duration_minutes": 10080,
                    "price_usd": Decimal("25.00"),
                },
            ]

            demo_plan_objs = []
            for plan_def in demo_plans:
                plan = Plan(
                    id=uuid4(),
                    tenant_id=demo_tenant.id,
                    name=plan_def["name"],
                    duration_minutes=plan_def["duration_minutes"],
                    price_usd=plan_def["price_usd"],
                    is_active=True,
                )
                session.add(plan)
                demo_plan_objs.append(plan)
            print(f"✓ {len(demo_plans)} planes creados")

            # Nodos para cuenta demo
            demo_nodes = [
                {
                    "name": "Bus 101 - Caracas a Maracay",
                    "serial_number": "SN-DEMO-001",
                    "location_name": "Ruta Caracas-Maracay",
                    "latitude": 10.4806,
                    "longitude": -66.9036,
                },
                {
                    "name": "Bus 202 - Caracas a Valencia",
                    "serial_number": "SN-DEMO-002",
                    "location_name": "Ruta Caracas-Valencia",
                    "latitude": 10.3910,
                    "longitude": -67.9365,
                },
                {
                    "name": "Evento - Plaza Mayor",
                    "serial_number": "SN-DEMO-003",
                    "location_name": "Plaza Mayor, Centro de Caracas",
                    "latitude": 10.5064,
                    "longitude": -66.5720,
                },
            ]

            demo_node_objs = []
            for node_def in demo_nodes:
                node = Node(
                    id=uuid4(),
                    tenant_id=demo_tenant.id,
                    name=node_def["name"],
                    serial=node_def["serial_number"],
                    location={
                        "lat": node_def["latitude"],
                        "lng": node_def["longitude"],
                        "address": node_def["location_name"],
                        "description": ""
                    },
                    status="online",
                    api_key=f"sk_demo_{uuid4().hex[:16]}",
                    last_seen_at=datetime.now(timezone.utc),
                )
                session.add(node)
                demo_node_objs.append(node)
            print(f"✓ {len(demo_nodes)} nodos creados\n")

            # =================================================================
            # 2. CREAR TENANT ADMIN (Para el sistema)
            # =================================================================
            print("2️⃣  CUENTA ADMIN (Sistema)")
            print("-" * 50)

            admin_tenant = Tenant(
                id=uuid4(),
                name="JADS Studio",
                slug="jads-studio",
                is_active=True,
                plan_tier="pro",
                subscription_status="active",
            )
            session.add(admin_tenant)
            print(f"✓ Tenant creado: {admin_tenant.name}")

            # Usuario admin
            admin_user = User(
                id=uuid4(),
                email="admin@jads.com",
                password_hash=pwd_context.hash("admin123456"),
                role="superadmin",
                tenant_id=admin_tenant.id,
                is_active=True,
            )
            session.add(admin_user)
            print("✓ Usuario creado: admin@jads.com (password: admin123456)\n")

            # Hacer flush para obtener los IDs generados
            await session.flush()

            # =================================================================
            # 3. CREAR TICKETS Y SESIONES DEMO
            # =================================================================
            print("3️⃣  TICKETS Y SESIONES DEMO")
            print("-" * 50)

            # Crear 5 tickets de ejemplo para el primer nodo
            tickets_created = 0
            for i in range(5):
                code = f"DEMO{uuid4().hex[:4].upper()}"
                ticket = Ticket(
                    id=uuid4(),
                    tenant_id=demo_tenant.id,
                    plan_id=demo_plan_objs[i % len(demo_plan_objs)].id,
                    node_id=demo_node_objs[0].id,
                    code=code,
                    qr_data=f"https://jadslink.io/activate/{code}",
                    status="active",
                    payment_method="cash",
                    activated_at=datetime.now(timezone.utc) - timedelta(hours=i),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=(12 - i)),
                )
                session.add(ticket)
                tickets_created += 1

            print(f"✓ {tickets_created} tickets creados")
            print("  (Las sesiones se crean cuando los usuarios activan tickets)\n")

            await session.commit()
            print("=" * 50)
            print("✅ SEED COMPLETADO EXITOSAMENTE")
            print("=" * 50)
            print()
            print("📋 CREDENCIALES DE ACCESO:")
            print()
            print("  DEMO (Demostración Pública):")
            print("  • Email:    demo@jadslink.com")
            print("  • Password: demo123456")
            print("  • Uso:      Para presentaciones y demos públicas")
            print()
            print("  ADMIN (Administrador del Sistema):")
            print("  • Email:    admin@jads.com")
            print("  • Password: admin123456")
            print("  • Uso:      Para gestión del sistema")
            print()
            print("🌐 Accede en: http://localhost:5173/login")
            print()


async def main():
    try:
        await drop_all_tables()
        await create_all_tables()
        await seed_demo_data()
    except Exception as e:
        print(f"\n❌ Error durante seed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
