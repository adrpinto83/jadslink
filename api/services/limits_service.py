"""Service for checking plan limits and restrictions."""

from models.tenant import Tenant, PlanTier
from models.pricing_config import PricingConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.node import Node
from models.ticket import Ticket
from decimal import Decimal


class LimitsService:
    """Servicio para verificar límites de planes según el tenant."""

    @staticmethod
    async def get_pricing_config(db: AsyncSession) -> PricingConfig:
        """Get the current global pricing configuration."""
        result = await db.execute(select(PricingConfig))
        config = result.scalar_one_or_none()
        if not config:
            # Create default config if it doesn't exist
            default_config = PricingConfig(
                ticket_pack_size=50,
                ticket_pack_price_usd=Decimal("0.50"),
                additional_node_price_usd=Decimal("50.00"),
                free_plan_max_nodes=1,
                free_plan_max_tickets=50,
                basic_plan_max_nodes=1,
                basic_plan_max_free_tickets=50,
            )
            db.add(default_config)
            await db.flush()
            return default_config
        return config

    @staticmethod
    async def can_create_node(tenant: Tenant, db: AsyncSession) -> tuple[bool, str]:
        """
        Verifica si el tenant puede crear un nodo nuevo.

        Retorna: (can_create: bool, message: str)
        """
        # Get pricing configuration
        pricing = await LimitsService.get_pricing_config(db)

        # Contar nodos activos del tenant
        result = await db.execute(
            select(func.count(Node.id)).where(
                Node.tenant_id == tenant.id,
                Node.deleted_at == None
            )
        )
        active_nodes = result.scalar() or 0

        # Determine max nodes based on plan and pricing config
        if tenant.plan_tier == PlanTier.starter:
            max_nodes = pricing.free_plan_max_nodes
        elif tenant.plan_tier == PlanTier.pro:
            max_nodes = pricing.basic_plan_max_nodes
        else:  # enterprise
            max_nodes = 999999

        if active_nodes >= max_nodes:
            if tenant.plan_tier == PlanTier.starter:
                return False, f"Plan Starter permite máximo {max_nodes} nodo. Upgrade a Pro para más nodos."
            elif tenant.plan_tier == PlanTier.pro:
                return False, f"Plan Pro permite máximo {max_nodes} nodos. Contacta soporte para Enterprise."
            else:
                return False, "No puedes crear más nodos."

        return True, "Puedes crear un nodo"

    @staticmethod
    async def can_generate_tickets(
        tenant: Tenant,
        quantity: int,
        db: AsyncSession
    ) -> tuple[bool, str]:
        """
        Verifica si el tenant puede generar N tickets.

        Retorna: (can_generate: bool, message: str)
        """
        if tenant.plan_tier == PlanTier.pro:
            return True, "Plan Pro - Tickets ilimitados"

        # Get pricing configuration
        pricing = await LimitsService.get_pricing_config(db)

        # Para Free y Basic: verificar disponibilidad
        available = tenant.get_available_tickets()

        if quantity <= available:
            return True, f"Usarás {quantity} tickets gratuitos"

        # Si quiere más, verificar si tiene pagos extras
        remaining_free = available
        needed_paid = quantity - available
        available_paid = tenant.extra_tickets_count * pricing.ticket_pack_size

        if needed_paid <= available_paid:
            packs_needed = (needed_paid + pricing.ticket_pack_size - 1) // pricing.ticket_pack_size
            cost_usd = packs_needed * pricing.ticket_pack_price_usd
            return True, f"Usarás {remaining_free} gratis + {needed_paid} pagos ($${float(cost_usd):.2f})"

        # No tiene suficientes
        if tenant.plan_tier == PlanTier.starter:
            total_available = tenant.free_tickets_limit + (tenant.extra_tickets_count * pricing.ticket_pack_size)
            return False, (
                f"No tienes suficientes tickets. "
                f"Disponibles: {total_available}. Necesitas: {quantity}. "
                f"Compra {pricing.ticket_pack_size} tickets adicionales por ${float(pricing.ticket_pack_price_usd):.2f}"
            )

        return False, f"Necesitas {needed_paid - available_paid} tickets más"

    @staticmethod
    async def record_ticket_generation(
        tenant: Tenant,
        quantity: int,
        db: AsyncSession
    ) -> dict:
        """
        Registra la generación de tickets y actualiza los contadores.
        Retorna información sobre cómo se cobró (free vs paid).
        """
        result = {
            "free_used": 0,
            "paid_used": 0,
            "cost_usd": 0.0,
        }

        if tenant.plan_tier == PlanTier.pro:
            return result  # Pro no tiene tracking

        # Contar cuántos gratis se usan
        free_available = tenant.get_available_tickets()
        result["free_used"] = min(quantity, free_available)
        tenant.free_tickets_used += result["free_used"]

        # El resto son pagos
        result["paid_used"] = quantity - result["free_used"]
        if result["paid_used"] > 0:
            result["cost_usd"] = (result["paid_used"] / 50) * 0.50

        await db.flush()
        return result
