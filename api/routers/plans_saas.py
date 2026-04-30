"""Router para obtener los planes SaaS disponibles."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.pricing_plan import PricingPlan
from schemas.pricing import SaaSPlanInfo, PlanFeature

router = APIRouter()


def _format_support_level(level: str) -> str:
    """Formatear el nivel de soporte al español"""
    mapping = {
        "email_48h": "Soporte Email (48h)",
        "email_24h": "Soporte Email prioritario (24h)",
        "chat_12h": "Email + Chat (12h)",
        "phone_24_7": "Soporte 24/7 (Teléfono + WhatsApp)",
    }
    return mapping.get(level, level)


def _format_retention(days: int) -> str:
    """Formatear los días de retención de datos"""
    if days < 0:
        return "ilimitado"
    elif days >= 365:
        years = days // 365
        return f"{years} año{'s' if years > 1 else ''}"
    elif days >= 30:
        months = days // 30
        return f"{months} mes{'es' if months > 1 else ''}"
    else:
        return f"{days} días"


def _build_plan_features(plan: PricingPlan) -> list[PlanFeature]:
    """Construir lista de features basada en el plan"""
    features = []

    # Tickets
    if plan.is_tickets_unlimited:
        features.append(
            PlanFeature(icon="ticket", text="Tickets ilimitados", included=True)
        )
    else:
        features.append(
            PlanFeature(
                icon="ticket",
                text=f"{plan.included_tickets_per_month} tickets/mes incluidos",
                included=True,
            )
        )

    # Nodos
    if plan.is_nodes_unlimited:
        features.append(
            PlanFeature(icon="server", text="Nodos ilimitados", included=True)
        )
    else:
        s = "s" if plan.included_nodes > 1 else ""
        features.append(
            PlanFeature(
                icon="server",
                text=f"{plan.included_nodes} nodo{s} incluido{s}",
                included=True,
            )
        )

    # API
    if plan.has_api_access:
        level = "completo" if plan.api_access_level == "full" else "básico"
        features.append(
            PlanFeature(icon="code", text=f"API access {level}", included=True)
        )
    else:
        features.append(
            PlanFeature(icon="code", text="API access", included=False)
        )

    # Soporte
    features.append(
        PlanFeature(
            icon="headphones",
            text=_format_support_level(plan.support_level),
            included=True,
        )
    )

    # Reportes
    features.append(
        PlanFeature(
            icon="chart",
            text=f"Reportes {plan.reports_level.lower()}",
            included=True,
        )
    )

    # Retención de datos
    features.append(
        PlanFeature(
            icon="database",
            text=f"Historial {_format_retention(plan.data_retention_days)}",
            included=True,
        )
    )

    return features


@router.get("/", response_model=list[SaaSPlanInfo])
async def get_saas_plans(db: AsyncSession = Depends(get_db)):
    """
    Obtener todos los planes SaaS activos para mostrar en login, billing, etc.
    Endpoint público (no requiere autenticación).
    """
    result = await db.execute(
        select(PricingPlan)
        .where(PricingPlan.is_active == True)
        .order_by(PricingPlan.sort_order)
    )
    plans = result.scalars().all()

    response = []
    for plan in plans:
        # Construir features dinámicas
        features = _build_plan_features(plan)

        # Formatear precios
        if plan.monthly_price > 0:
            monthly_display = f"${plan.monthly_price:.0f}/mes"
        else:
            monthly_display = "$0"

        # Tickets
        if plan.is_tickets_unlimited:
            tickets_display = "Ilimitados"
        elif plan.additional_ticket_pack_price:
            price = plan.additional_ticket_pack_price
            tickets_display = f"${price:.0f} c/{plan.additional_ticket_pack_size} tickets"
        else:
            tickets_display = "No disponible"

        # Nodos
        if plan.is_nodes_unlimited:
            nodes_display = "Ilimitados"
        elif plan.additional_node_price:
            nodes_display = f"${plan.additional_node_price:.0f}/mes por nodo"
        else:
            nodes_display = "No disponible"

        # Determinar badge
        badge = None
        if plan.is_recommended:
            badge = "Más Popular"
        elif plan.tier == "standard":
            badge = "Mejor Valor"

        response.append(
            SaaSPlanInfo(
                tier=plan.tier,
                name=plan.name,
                description=plan.description,
                monthly_price=plan.monthly_price,
                monthly_price_display=monthly_display,
                included_tickets=plan.included_tickets_per_month,
                additional_tickets_price=plan.additional_ticket_pack_price,
                additional_tickets_display=tickets_display,
                is_tickets_unlimited=plan.is_tickets_unlimited,
                included_nodes=plan.included_nodes,
                additional_node_price=plan.additional_node_price,
                additional_node_display=nodes_display,
                is_nodes_unlimited=plan.is_nodes_unlimited,
                features=features,
                support_level=_format_support_level(plan.support_level),
                has_api_access=plan.has_api_access,
                reports_level=plan.reports_level.capitalize(),
                data_retention=_format_retention(plan.data_retention_days),
                icon=plan.icon,
                color=plan.color,
                is_recommended=plan.is_recommended,
                badge=badge,
            )
        )

    return response
