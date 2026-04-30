#!/usr/bin/env python3
"""Script autónomo para crear los 4 planes SaaS en la base de datos.
No depende de imports relativos ni .env - se puede ejecutar desde cualquier lugar.
"""

import asyncio
import sys
import os
from decimal import Decimal
from pathlib import Path

# Buscar .env en directorios conocidos
env_paths = [
    Path("/home/u938946830/jadslink-deploy/api/.env"),  # Hostinger
    Path("/home/adrpinto/jadslink/api/.env"),            # Local
    Path("./api/.env"),                                   # Actual
    Path(".env"),                                         # Cwd
]

env_file = None
for path in env_paths:
    if path.exists():
        env_file = path
        break

if not env_file:
    print("❌ Error: No se encontró archivo .env")
    print("   Directorios buscados:")
    for path in env_paths:
        print(f"     - {path}")
    sys.exit(1)

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv(env_file)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Numeric, Integer, Boolean, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Definir modelo directamente (evitar imports complicados)
Base = declarative_base()

class PricingPlan(Base):
    __tablename__ = "pricing_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tier = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    monthly_price = Column(Numeric(10, 2), nullable=False)
    included_tickets_per_month = Column(Integer, nullable=False)
    additional_ticket_pack_size = Column(Integer, default=100)
    additional_ticket_pack_price = Column(Numeric(10, 2))
    is_tickets_unlimited = Column(Boolean, default=False)
    included_nodes = Column(Integer, default=1)
    additional_node_price = Column(Numeric(10, 2))
    is_nodes_unlimited = Column(Boolean, default=False)
    has_api_access = Column(Boolean, default=False)
    api_access_level = Column(String(50))
    support_level = Column(String(50))
    reports_level = Column(String(50))
    data_retention_days = Column(Integer, default=30)
    icon = Column(String(50), default="wifi")
    color = Column(String(50), default="blue")
    is_recommended = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

DATABASE_URL = os.getenv('DATABASE_URL')

async def seed_pricing_plans():
    """Crear los 4 planes SaaS en la base de datos"""

    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL no configurado en .env")
        sys.exit(1)

    print(f"📁 Cargando desde: {env_file}")
    print(f"🔗 Base de datos: {DATABASE_URL[:50]}...")

    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            # Verificar si la tabla existe
            from sqlalchemy import inspect, text

            try:
                result = await db.execute(text("SELECT COUNT(*) FROM pricing_plans"))
                count = result.scalar()

                if count > 0:
                    print(f"⚠️  Ya existen {count} planes en la BD")
                    print("   Eliminando planes antiguos...")
                    await db.execute(text("DELETE FROM pricing_plans"))
                    await db.commit()
            except Exception as e:
                print(f"⚠️  Tabla no existe aún (normal en primera ejecución): {e}")

            # Crear 4 planes
            plans = [
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
                db.add(plan)

            await db.commit()

            # Verificar que se crearon
            result = await db.execute(text("SELECT COUNT(*) FROM pricing_plans"))
            final_count = result.scalar()

            print(f"\n✅ {final_count} planes SaaS creados exitosamente:")
            print("   • Gratuito: $0/mes (50 tickets)")
            print("   • Básico: $29/mes (200 tickets)")
            print("   • Estándar: $79/mes (1,000 tickets, 3 nodos) ⭐")
            print("   • Pro: $199/mes (Ilimitado)")

            return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(seed_pricing_plans())
    sys.exit(0 if success else 1)
