"""Admin endpoints for managing pricing configuration."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.pricing_config import PricingConfig
from models.user import User
from schemas.pricing import PricingConfigUpdate, PricingConfigResponse
from database import get_db
from deps import get_superadmin

router = APIRouter()


@router.get("", response_model=PricingConfigResponse)
async def get_pricing_config(
    db: AsyncSession = Depends(get_db),
):
    """Get current global pricing configuration (public endpoint)."""
    result = await db.execute(select(PricingConfig))
    config = result.scalar_one_or_none()

    if not config:
        # Create default config if it doesn't exist
        default_config = PricingConfig(
            ticket_pack_size=50,
            ticket_pack_price_usd=0.50,
            additional_node_price_usd=50.00,
            free_plan_max_nodes=1,
            free_plan_max_tickets=50,
            basic_plan_max_nodes=1,
            basic_plan_max_free_tickets=50,
        )
        db.add(default_config)
        await db.commit()
        await db.refresh(default_config)
        return default_config

    return config


@router.patch("", response_model=PricingConfigResponse)
async def update_pricing_config(
    config_update: PricingConfigUpdate,
    _: User = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Update global pricing configuration (superadmin only)."""
    result = await db.execute(select(PricingConfig))
    config = result.scalar_one_or_none()

    if not config:
        # Create default config if it doesn't exist
        config = PricingConfig(
            ticket_pack_size=50,
            ticket_pack_price_usd=0.50,
            additional_node_price_usd=50.00,
            free_plan_max_nodes=1,
            free_plan_max_tickets=50,
            basic_plan_max_nodes=1,
            basic_plan_max_free_tickets=50,
        )
        db.add(config)
        await db.flush()

    # Update only provided fields
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return config
