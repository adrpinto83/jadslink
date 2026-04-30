#!/usr/bin/env python3
"""
Script de migración manual para crear tabla pricing_plans e insertar datos.
Útil cuando Alembic no está disponible o en ambiente de desarrollo.
"""

import asyncio
import sys
import os
from decimal import Decimal
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env before importing config
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

try:
    from config import get_settings
except:
    pass

from models.pricing_plan import PricingPlan
from models.base import Base


async def create_table(engine):
    """Crear la tabla pricing_plans si no existe"""
    print("📋 Creando tabla pricing_plans...")

    async with engine.begin() as conn:
        # Crear tabla (idempotente)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pricing_plans (
                id CHAR(36) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP NULL,
                tier VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                monthly_price DECIMAL(10, 2) NOT NULL,
                included_tickets_per_month INT NOT NULL,
                additional_ticket_pack_size INT DEFAULT 100,
                additional_ticket_pack_price DECIMAL(10, 2),
                is_tickets_unlimited BOOLEAN DEFAULT FALSE,
                included_nodes INT DEFAULT 1,
                additional_node_price DECIMAL(10, 2),
                is_nodes_unlimited BOOLEAN DEFAULT FALSE,
                has_api_access BOOLEAN DEFAULT FALSE,
                api_access_level VARCHAR(50) DEFAULT 'none',
                support_level VARCHAR(50) NOT NULL,
                reports_level VARCHAR(50) DEFAULT 'basic',
                data_retention_days INT DEFAULT 30,
                icon VARCHAR(50) DEFAULT 'wifi',
                color VARCHAR(50) DEFAULT 'blue',
                is_recommended BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INT DEFAULT 0,
                INDEX ix_pricing_plans_tier (tier),
                INDEX ix_pricing_plans_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    print("✅ Tabla pricing_plans lista")


async def seed_plans(session: AsyncSession):
    """Insertar los 4 planes SaaS"""
    print("\n🌱 Insertando planes SaaS...")

    # Verificar si ya existen
    from sqlalchemy import select
    result = await session.execute(select(PricingPlan))
    existing_plans = result.scalars().all()

    if existing_plans:
        print(f"⚠️  Ya hay {len(existing_plans)} planes en la BD. Eliminando...")
        for plan in existing_plans:
            await session.delete(plan)
        await session.commit()

    plans = [
        # PLAN GRATUITO
        PricingPlan(
            tier="free",
            name="Gratuito",
            description="Perfecto para probar el sistema sin compromiso",
            monthly_price=Decimal("0.00"),
            included_tickets_per_month=50,
            additional_ticket_pack_size=100,
            additional_ticket_pack_price=None,
            is_tickets_unlimited=False,
            included_nodes=1,
            additional_node_price=None,
            is_nodes_unlimited=False,
            has_api_access=False,
            api_access_level="none",
            support_level="email_48h",
            reports_level="basic",
            data_retention_days=30,
            icon="wifi",
            color="gray",
            is_recommended=False,
            is_active=True,
            sort_order=0,
        ),
        # PLAN BÁSICO
        PricingPlan(
            tier="basic",
            name="Básico",
            description="Ideal para empezar con 1 nodo y tráfico moderado",
            monthly_price=Decimal("29.00"),
            included_tickets_per_month=200,
            additional_ticket_pack_size=100,
            additional_ticket_pack_price=Decimal("8.00"),
            is_tickets_unlimited=False,
            included_nodes=1,
            additional_node_price=Decimal("40.00"),
            is_nodes_unlimited=False,
            has_api_access=False,
            api_access_level="none",
            support_level="email_24h",
            reports_level="basic",
            data_retention_days=90,
            icon="zap",
            color="blue",
            is_recommended=False,
            is_active=True,
            sort_order=1,
        ),
        # PLAN ESTÁNDAR
        PricingPlan(
            tier="standard",
            name="Estándar",
            description="Perfecto para crecer: 3 nodos y alto volumen de tickets",
            monthly_price=Decimal("79.00"),
            included_tickets_per_month=1000,
            additional_ticket_pack_size=100,
            additional_ticket_pack_price=Decimal("6.00"),
            is_tickets_unlimited=False,
            included_nodes=3,
            additional_node_price=Decimal("30.00"),
            is_nodes_unlimited=False,
            has_api_access=True,
            api_access_level="basic",
            support_level="chat_12h",
            reports_level="advanced",
            data_retention_days=365,
            icon="trending-up",
            color="purple",
            is_recommended=True,
            is_active=True,
            sort_order=2,
        ),
        # PLAN PRO
        PricingPlan(
            tier="pro",
            name="Pro",
            description="Sin límites: para empresas que necesitan escalar sin preocupaciones",
            monthly_price=Decimal("199.00"),
            included_tickets_per_month=999999,
            additional_ticket_pack_size=100,
            additional_ticket_pack_price=None,
            is_tickets_unlimited=True,
            included_nodes=999,
            additional_node_price=None,
            is_nodes_unlimited=True,
            has_api_access=True,
            api_access_level="full",
            support_level="phone_24_7",
            reports_level="custom",
            data_retention_days=-1,
            icon="crown",
            color="gold",
            is_recommended=False,
            is_active=True,
            sort_order=3,
        ),
    ]

    for plan in plans:
        session.add(plan)

    await session.commit()
    print("✅ 4 planes SaaS creados exitosamente:")
    print("   • Gratuito: $0 (50 tickets/mes)")
    print("   • Básico: $29 (200 tickets/mes)")
    print("   • Estándar: $79 (1,000 tickets/mes, 3 nodos) [RECOMENDADO]")
    print("   • Pro: $199 (Ilimitado)")


async def main():
    """Ejecutar migración y seed"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+aiomysql://user:password@localhost:3306/jads')

    print("=" * 60)
    print("🚀 MIGRACIÓN E INSERCIÓN DE PLANES SAAS")
    print("=" * 60)
    print(f"\n📊 Database: {DATABASE_URL[:50]}...\n")

    try:
        # Crear engine
        engine = create_async_engine(DATABASE_URL, echo=False)

        # Crear tabla
        await create_table(engine)

        # Crear session
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Insertar planes
            await seed_plans(session)

        # Verificar
        async with async_session() as session:
            result = await session.execute(text("SELECT COUNT(*) as count FROM pricing_plans"))
            count = result.scalar()
            print(f"\n✅ VERIFICACIÓN: {count} planes en la BD\n")

        await engine.dispose()

        print("=" * 60)
        print("✅ ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print("=" * 60)
        print("\n🎯 Próximos pasos:")
        print("   1. Reinicia el API: python3 -m uvicorn api.main:app --reload")
        print("   2. Verifica el endpoint: curl http://localhost:8000/api/v1/saas-plans")
        print("   3. Abre el dashboard: http://localhost:5173/login\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error durante migración: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
