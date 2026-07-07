"""
Rutas para gestión de tasas de cambio USD -> Bs
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import requests
import re

from ..database import get_db
from ..models import ExchangeRate
from ..models import User
from ..routes.auth import get_current_user, require_superadmin

router = APIRouter(prefix="/api/exchange", tags=["exchange"])


# Cache simple en memoria (se reinicia con el servidor)
_rate_cache = {
    "rate": None,
    "timestamp": None,
    "ttl_minutes": 60  # Cache por 1 hora
}


def get_cached_rate(db: Session) -> Optional[Decimal]:
    """
    Obtiene la tasa desde cache si es válida, sino desde BD
    """
    now = datetime.utcnow()

    # Verificar cache en memoria
    if _rate_cache["rate"] and _rate_cache["timestamp"]:
        age_minutes = (now - _rate_cache["timestamp"]).total_seconds() / 60
        if age_minutes < _rate_cache["ttl_minutes"]:
            return _rate_cache["rate"]

    # Cache expirado o no existe, consultar BD
    latest = db.query(ExchangeRate).filter(
        ExchangeRate.is_active == True
    ).order_by(ExchangeRate.created_at.desc()).first()

    if latest:
        # Actualizar cache
        _rate_cache["rate"] = latest.rate
        _rate_cache["timestamp"] = now
        return latest.rate

    return None


@router.get("/current")
def get_current_rate(db: Session = Depends(get_db)):
    """
    Obtiene la tasa de cambio actual USD -> Bs

    Endpoint público (sin autenticación)
    Cache: 1 hora en memoria
    """
    rate = get_cached_rate(db)

    if rate is None:
        # No hay tasa en BD, devolver tasa por defecto
        rate = Decimal("36.50")
        source = "default"
        updated_at = None
    else:
        # Obtener info de la última tasa
        latest = db.query(ExchangeRate).filter(
            ExchangeRate.is_active == True
        ).order_by(ExchangeRate.created_at.desc()).first()
        source = latest.source if latest else "unknown"
        updated_at = latest.created_at.isoformat() if latest else None

    return {
        "rate": float(rate),
        "source": source,
        "updated_at": updated_at,
        "cached": _rate_cache["rate"] is not None
    }


@router.get("/history")
def get_rate_history(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene historial de tasas de cambio

    Requiere autenticación
    """
    rates = db.query(ExchangeRate).order_by(
        ExchangeRate.created_at.desc()
    ).limit(limit).all()

    return {
        "rates": [
            {
                "rate": float(r.rate),
                "source": r.source,
                "source_url": r.source_url,
                "is_active": r.is_active,
                "updated_by": r.updated_by,
                "notes": r.notes,
                "created_at": r.created_at.isoformat()
            }
            for r in rates
        ]
    }


@router.post("/update")
def manual_update_rate(
    rate: float,
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """
    Actualización manual de la tasa de cambio

    Solo superadmin
    """
    if rate <= 0:
        raise HTTPException(status_code=400, detail="La tasa debe ser mayor a 0")

    if rate < 10:
        raise HTTPException(
            status_code=400,
            detail="La tasa parece muy baja. Por favor verifica el valor."
        )

    # Desactivar tasas anteriores
    db.query(ExchangeRate).update({"is_active": False})

    # Crear nueva tasa
    new_rate = ExchangeRate(
        rate=Decimal(str(rate)),
        source="manual",
        source_url=None,
        is_active=True,
        updated_by=current_user.email,
        notes=note or f"Actualización manual por {current_user.email}"
    )

    db.add(new_rate)
    db.commit()
    db.refresh(new_rate)

    # Limpiar cache
    _rate_cache["rate"] = None
    _rate_cache["timestamp"] = None

    return {
        "ok": True,
        "message": f"Tasa actualizada a {rate} Bs/USD",
        "rate": {
            "rate": float(new_rate.rate),
            "source": new_rate.source,
            "updated_by": new_rate.updated_by,
            "created_at": new_rate.created_at.isoformat()
        }
    }


@router.post("/refresh")
def refresh_from_bcv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """
    Fuerza actualización desde BCV

    Solo superadmin
    """
    try:
        # Intentar BCV
        rate, source_url = _scrape_bcv()
        source = "bcv_scraping"
    except Exception as e:
        # Fallback a API
        try:
            rate, source_url = _get_api_fallback()
            source = "api_fallback"
        except Exception as e2:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo obtener tasa: BCV error: {str(e)}, API error: {str(e2)}"
            )

    # Desactivar tasas anteriores
    db.query(ExchangeRate).update({"is_active": False})

    # Crear nueva tasa
    new_rate = ExchangeRate(
        rate=rate,
        source=source,
        source_url=source_url,
        is_active=True,
        updated_by=current_user.email,
        notes=f"Actualización manual forzada desde {source}"
    )

    db.add(new_rate)
    db.commit()
    db.refresh(new_rate)

    # Limpiar cache
    _rate_cache["rate"] = None
    _rate_cache["timestamp"] = None

    return {
        "ok": True,
        "message": f"Tasa actualizada desde {source}",
        "rate": {
            "rate": float(new_rate.rate),
            "source": new_rate.source,
            "source_url": new_rate.source_url,
            "created_at": new_rate.created_at.isoformat()
        }
    }


def _scrape_bcv() -> tuple[Decimal, str]:
    """Scraping del BCV"""
    url = "https://www.bcv.org.ve/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    patterns = [
        r'<strong[^>]*>(\d+[,\.]\d+)<\/strong>',
        r'dolar.*?(\d+[,\.]\d+)',
        r'USD.*?(\d+[,\.]\d+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, response.text, re.IGNORECASE)
        if matches:
            for match in matches:
                rate_str = match.replace(',', '.')
                try:
                    rate = Decimal(rate_str)
                    if rate > 10:
                        return rate, url
                except:
                    continue

    raise ValueError("No se encontró tasa en BCV")


def _get_api_fallback() -> tuple[Decimal, str]:
    """API de fallback"""
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    rate = None
    if 'VES' in data['rates']:
        rate = Decimal(str(data['rates']['VES']))
    elif 'VEF' in data['rates']:
        rate = Decimal(str(data['rates']['VEF']))

    if rate and rate > 10:
        return rate, url

    raise ValueError("No se encontró VES/VEF en API")
