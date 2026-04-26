"""Utility endpoints: exchange rates, health checks, etc."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

from database import get_db
from deps import get_superadmin
from models.user import User
from services.exchange_rate_service import ExchangeRateService
import logging

log = logging.getLogger("jadslink.utils")

router = APIRouter()


class ExchangeRateUpdate(BaseModel):
    """Schema for updating exchange rate"""

    rate: Decimal = Field(..., gt=0, decimal_places=4, description="New exchange rate USD -> VEF")
    notes: str | None = Field(None, description="Optional notes about the update")


@router.get("/exchange-rate")
async def get_current_exchange_rate(db: AsyncSession = Depends(get_db)):
    """
    Get current exchange rate USD -> VEF.
    Publicly accessible endpoint used by frontend.

    Returns:
        {
            "rate": 36.50,
            "source": "bcv_scraping" | "api_fallback" | "manual",
            "updated_at": "2026-04-26T19:00:00Z"
        }
    """
    rate = await ExchangeRateService.get_current_rate(db)

    # Get metadata about the current rate
    from sqlalchemy import select
    from models.exchange_rate import ExchangeRate

    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.is_active == True)
        .order_by(ExchangeRate.created_at.desc())
        .limit(1)
    )
    rate_record = result.scalar_one_or_none()

    if rate_record:
        return {
            "rate": float(rate_record.rate),
            "source": rate_record.source,
            "updated_at": rate_record.created_at.isoformat(),
        }

    return {
        "rate": float(rate),
        "source": "default",
        "updated_at": datetime.now().isoformat(),
    }


@router.post("/exchange-rate/admin-update")
async def admin_update_exchange_rate(
    data: ExchangeRateUpdate,
    current_user: User = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin endpoint to manually update exchange rate.
    Only superadmin can use this.

    Example:
    POST /api/v1/utils/exchange-rate/admin-update
    {
        "rate": 37.50,
        "notes": "Official BCV rate updated"
    }
    """
    try:
        new_rate = await ExchangeRateService.set_manual_rate(
            db=db,
            rate=data.rate,
            admin_email=current_user.email,
            notes=data.notes,
        )

        await db.commit()
        await db.refresh(new_rate)

        log.info(f"Exchange rate updated to {data.rate} by {current_user.email}")

        return {
            "success": True,
            "message": f"Tasa actualizada a {data.rate} VEF por USD",
            "rate": float(new_rate.rate),
            "source": new_rate.source,
            "updated_at": new_rate.created_at.isoformat(),
        }

    except Exception as e:
        log.error(f"Error updating exchange rate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar tasa: {str(e)}",
        )


@router.post("/exchange-rate/fetch-from-api")
async def fetch_exchange_rate_from_api(
    current_user: User = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin endpoint to fetch exchange rate from external API.
    Tries to update from fallback API (exchangerate-api.com).
    """
    try:
        success, rate, source = await ExchangeRateService.fetch_from_fallback_api()

        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not fetch rate from API: {source}",
            )

        await db.commit()

        log.info(f"Exchange rate fetched from API: {rate} by {current_user.email}")

        return {
            "success": True,
            "message": f"Tasa actualizada desde API: {rate}",
            "rate": float(rate),
            "source": source,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error fetching rate from API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}",
        )
