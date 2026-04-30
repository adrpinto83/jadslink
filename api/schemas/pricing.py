"""Schemas for pricing configuration."""

from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime


class PricingConfigUpdate(BaseModel):
    """Schema for updating pricing configuration"""
    ticket_pack_size: int | None = Field(None, ge=1)
    ticket_pack_price_usd: Decimal | None = Field(None, ge=Decimal("0.01"))
    additional_node_price_usd: Decimal | None = Field(None, ge=Decimal("0.01"))
    free_plan_max_nodes: int | None = Field(None, ge=1)
    free_plan_max_tickets: int | None = Field(None, ge=1)
    basic_plan_max_nodes: int | None = Field(None, ge=1)
    basic_plan_max_free_tickets: int | None = Field(None, ge=1)
    description: str | None = Field(None, max_length=500)


class PricingConfigResponse(BaseModel):
    """Schema for pricing configuration response"""
    id: UUID
    ticket_pack_size: int
    ticket_pack_price_usd: Decimal
    additional_node_price_usd: Decimal
    free_plan_max_nodes: int
    free_plan_max_tickets: int
    basic_plan_max_nodes: int
    basic_plan_max_free_tickets: int
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanFeature(BaseModel):
    """Representa una feature/característica de un plan"""

    icon: str = Field(..., description="Nombre del ícono (lucide-react)")
    text: str = Field(..., description="Texto descriptivo de la característica")
    included: bool = Field(..., description="Si está incluida en este plan")


class SaaSPlanInfo(BaseModel):
    """Información completa de un plan SaaS para mostrar en frontend"""

    # Identificación
    tier: str = Field(..., description="ID único del plan: free, basic, standard, pro")
    name: str = Field(..., description="Nombre mostrable: Gratuito, Básico, etc")
    description: str = Field(..., description="Descripción corta del plan")

    # Precios
    monthly_price: Decimal = Field(..., description="Precio mensual en USD")
    monthly_price_display: str = Field(
        ..., description="Precio formateado: $29/mes"
    )

    # Tickets
    included_tickets: int = Field(
        ..., description="Tickets incluidos por mes sin costo"
    )
    additional_tickets_price: Decimal | None = Field(
        None, description="Precio por pack adicional"
    )
    additional_tickets_display: str = Field(
        ..., description="Display: $8 c/100 tickets o Ilimitados"
    )
    is_tickets_unlimited: bool = Field(..., description="¿Tickets ilimitados?")

    # Nodos
    included_nodes: int = Field(..., description="Nodos incluidos en el plan")
    additional_node_price: Decimal | None = Field(
        None, description="Precio por nodo adicional"
    )
    additional_node_display: str = Field(
        ..., description="Display: $40/mes por nodo o Ilimitados"
    )
    is_nodes_unlimited: bool = Field(..., description="¿Nodos ilimitados?")

    # Features dinámicas
    features: list[PlanFeature] = Field(..., description="Lista de features del plan")

    # Características principales
    support_level: str = Field(..., description="Nivel de soporte formateado")
    has_api_access: bool = Field(..., description="¿Tiene acceso a API?")
    reports_level: str = Field(..., description="Nivel de reportes disponibles")
    data_retention: str = Field(
        ..., description="Retención de datos formateada: 30 días, 1 año, ilimitado"
    )

    # UI
    icon: str = Field(..., description="Nombre del ícono principal del plan")
    color: str = Field(..., description="Color hex o nombre de color Tailwind")
    is_recommended: bool = Field(False, description="¿Mostrar como recomendado?")
    badge: str | None = Field(None, description="Texto del badge: Más Popular, Mejor Valor")

    class Config:
        json_schema_extra = {
            "example": {
                "tier": "standard",
                "name": "Estándar",
                "description": "Perfecto para crecer: 3 nodos y alto volumen de tickets",
                "monthly_price": 79.0,
                "monthly_price_display": "$79/mes",
                "included_tickets": 1000,
                "additional_tickets_price": 6.0,
                "additional_tickets_display": "$6 c/100 tickets",
                "is_tickets_unlimited": False,
                "included_nodes": 3,
                "additional_node_price": 30.0,
                "additional_node_display": "$30/mes por nodo",
                "is_nodes_unlimited": False,
                "features": [
                    {
                        "icon": "ticket",
                        "text": "1,000 tickets/mes incluidos",
                        "included": True,
                    },
                    {
                        "icon": "server",
                        "text": "3 nodos incluidos",
                        "included": True,
                    },
                ],
                "support_level": "Email + Chat (12h)",
                "has_api_access": True,
                "reports_level": "Advanced",
                "data_retention": "1 año",
                "icon": "trending-up",
                "color": "purple",
                "is_recommended": True,
                "badge": "Más Popular",
            }
        }
