"""Script para crear los 4 planes SaaS en la base de datos."""

import asyncio
import sys
import os
from decimal import Decimal
from pathlib import Path

# Agregar el directorio api al path
api_dir = Path(__file__).parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(api_dir / '.env')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.pricing_plan import PricingPlan

DATABASE_URL = os.getenv('DATABASE_URL')


async def seed_pricing_plans():
    """Crear los 4 planes SaaS en la base de datos"""

    # Validar que tenemos DATABASE_URL
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL no está configurado")
        print(f"   Buscamos .env en: {api_dir / '.env'}")
        sys.exit(1)

    # Crear engine y session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            plans = [
                # PLAN GRATUITO
                PricingPlan(
                    tier="free",
                    name="Gratuito",
                    description="Perfecto para probar el sistema sin compromiso",
                    monthly_price=Decimal("0.00"),
                    included_tickets_per_month=50,
                    additional_ticket_pack_size=100,
                    additional_ticket_pack_price=None,  # Bloqueado
                    is_tickets_unlimited=False,
                    included_nodes=1,
                    additional_node_price=None,  # No disponible
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
                    is_recommended=True,  # Badge "Más Popular"
                    is_active=True,
                    sort_order=2,
                ),
                # PLAN PRO
                PricingPlan(
                    tier="pro",
                    name="Pro",
                    description="Sin límites: para empresas que necesitan escalar sin preocupaciones",
                    monthly_price=Decimal("199.00"),
                    included_tickets_per_month=999999,  # Representación de "ilimitado"
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
                    data_retention_days=-1,  # -1 = ilimitado
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
            print("✅ 4 planes SaaS creados exitosamente:")
            print("   • Gratuito: $0 (50 tickets/mes)")
            print("   • Básico: $29 (200 tickets/mes)")
            print("   • Estándar: $79 (1,000 tickets/mes, 3 nodos) [RECOMENDADO]")
            print("   • Pro: $199 (Ilimitado)")

        except Exception as e:
            print(f"❌ Error al crear planes: {e}")
            await db.rollback()
            sys.exit(1)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_pricing_plans())
