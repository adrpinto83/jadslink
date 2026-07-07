#!/usr/bin/env python3
"""
Script para actualizar automáticamente la tasa de cambio USD -> Bs desde el BCV
Se ejecuta diariamente mediante cron job en Hostinger
"""

import requests
import re
from decimal import Decimal
from datetime import datetime
import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from api.models import ExchangeRate


def get_bcv_rate() -> tuple[Decimal, str]:
    """
    Obtiene la tasa de cambio oficial del BCV mediante web scraping

    Returns:
        tuple[Decimal, str]: (tasa, url_fuente)
    """
    url = "https://www.bcv.org.ve/"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Buscar patrón: <strong>XX,XX</strong> (tasa del dólar)
        # El BCV usa formato venezolano con coma como separador decimal
        patterns = [
            r'<strong[^>]*>(\d+[,\.]\d+)<\/strong>',
            r'dolar.*?(\d+[,\.]\d+)',
            r'USD.*?(\d+[,\.]\d+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            if matches:
                # Tomar el primer número que parezca una tasa válida (> 10)
                for match in matches:
                    # Convertir coma a punto
                    rate_str = match.replace(',', '.')
                    try:
                        rate = Decimal(rate_str)
                        if rate > 10:  # Sanity check: tasa debe ser > 10 Bs
                            return rate, url
                    except:
                        continue

        raise ValueError("No se encontró tasa en el HTML del BCV")

    except Exception as e:
        print(f"❌ Error scraping BCV: {e}")
        raise


def get_exchangerate_api_fallback() -> tuple[Decimal, str]:
    """
    Obtiene tasa de cambio de API como fallback

    Returns:
        tuple[Decimal, str]: (tasa, url_fuente)
    """
    url = "https://api.exchangerate-api.com/v4/latest/USD"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Intentar VES (Bolívar Soberano actual) o VEF (antiguo)
        rate = None
        if 'VES' in data['rates']:
            rate = Decimal(str(data['rates']['VES']))
        elif 'VEF' in data['rates']:
            rate = Decimal(str(data['rates']['VEF']))

        if rate and rate > 10:
            return rate, url

        raise ValueError("No se encontró VES/VEF en la API")

    except Exception as e:
        print(f"❌ Error con API fallback: {e}")
        raise


def update_exchange_rate():
    """
    Actualiza la tasa de cambio en la base de datos
    """
    # Configuración de base de datos
    db_url = os.getenv('DATABASE_URL', 'sqlite:////home/u938946830/jadslink-app/data/hotspot.db')

    engine = create_engine(db_url)

    with Session(engine) as session:
        try:
            # Intentar primero con BCV
            print("📡 Consultando BCV...")
            rate, source_url = get_bcv_rate()
            source = "bcv_scraping"
            print(f"✓ Tasa BCV obtenida: {rate} Bs/USD")

        except Exception as e:
            print(f"⚠️  BCV no disponible, usando API fallback...")
            try:
                rate, source_url = get_exchangerate_api_fallback()
                source = "api_fallback"
                print(f"✓ Tasa API obtenida: {rate} Bs/USD")
            except Exception as e2:
                print(f"❌ Error con fallback: {e2}")
                print("❌ No se pudo obtener tasa de cambio")
                return False

        # Desactivar tasas anteriores
        session.query(ExchangeRate).update({"is_active": False})

        # Crear nueva tasa activa
        new_rate = ExchangeRate(
            rate=rate,
            source=source,
            source_url=source_url,
            is_active=True,
            updated_by="cron_job",
            notes=f"Actualización automática - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        session.add(new_rate)
        session.commit()

        print(f"✅ Tasa actualizada exitosamente: {rate} Bs/USD")
        print(f"   Fuente: {source}")
        print(f"   URL: {source_url}")

        return True


def main():
    """
    Función principal
    """
    print("="*60)
    print("  Actualización de Tasa de Cambio BCV")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    print()

    try:
        success = update_exchange_rate()

        if success:
            print()
            print("="*60)
            print("  ✅ Actualización completada exitosamente")
            print("="*60)
            sys.exit(0)
        else:
            print()
            print("="*60)
            print("  ❌ Error en la actualización")
            print("="*60)
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
