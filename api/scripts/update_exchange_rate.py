#!/usr/bin/env python3
"""
Script to manually update the exchange rate USD -> VEF.
Usage: python scripts/update_exchange_rate.py <rate> [notes]

Examples:
  python scripts/update_exchange_rate.py 37.50
  python scripts/update_exchange_rate.py 37.50 "Official BCV rate"
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import async_session_maker
from services.exchange_rate_service import ExchangeRateService


async def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python scripts/update_exchange_rate.py <rate> [notes]")
        print("Example: python scripts/update_exchange_rate.py 37.50")
        sys.exit(1)

    try:
        rate = Decimal(sys.argv[1])
    except ValueError:
        print(f"❌ Invalid rate: {sys.argv[1]}. Must be a number.")
        sys.exit(1)

    if rate <= 0:
        print("❌ Rate must be greater than 0")
        sys.exit(1)

    notes = sys.argv[2] if len(sys.argv) > 2 else None

    async with async_session_maker() as db:
        try:
            new_rate = await ExchangeRateService.set_manual_rate(
                db=db,
                rate=rate,
                admin_email="system",
                notes=notes or "Manual update via script",
            )

            await db.commit()

            print(f"✅ Exchange rate updated successfully!")
            print(f"   Rate: {new_rate.rate} VEF per USD")
            print(f"   Source: {new_rate.source}")
            print(f"   Notes: {new_rate.notes}")
            print(f"   Updated at: {new_rate.created_at}")

        except Exception as e:
            print(f"❌ Error updating rate: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
