"""Service for managing exchange rates USD -> VEF."""

import httpx
from bs4 import BeautifulSoup
from decimal import Decimal
from models.exchange_rate import ExchangeRate
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import logging

log = logging.getLogger("jadslink.exchange_rate")


class ExchangeRateService:
    """Service for managing exchange rates USD -> VEF (Bolívar venezolano)"""

    @staticmethod
    async def scrape_bcv_rate() -> tuple[bool, Decimal | None, str]:
        """
        Scrape BCV website for official exchange rate.
        BCV's HTML structure: <div class="col-sm-6 col-xs-6 centrado"><strong>484,74040000</strong></div>
        Returns (success, rate, source_or_error_message)
        """
        try:
            # Try with longer timeout and multiple User-Agents
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (compatible; JADSlink/1.0)",
            ]

            import re

            for user_agent in user_agents:
                try:
                    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                        response = await client.get(
                            "https://www.bcv.org.ve/",
                            headers={"User-Agent": user_agent},
                        )
                        response.raise_for_status()

                        html = response.text
                        soup = BeautifulSoup(html, "html.parser")

                        # Strategy 1: Look for the exact div class "col-sm-6 col-xs-6 centrado"
                        # This is the official rate container on BCV website
                        rate_element = soup.find("div", class_="col-sm-6 col-xs-6 centrado")

                        if rate_element:
                            strong_tag = rate_element.find("strong")
                            if strong_tag:
                                rate_text = strong_tag.get_text().strip()
                                # Convert comma to decimal point (484,74040000 -> 484.74040000)
                                rate_str = rate_text.replace(",", ".")
                                try:
                                    rate = Decimal(rate_str)
                                    if rate > 0:
                                        log.info(f"✅ BCV scraping successful: {rate} (User-Agent: {user_agent})")
                                        return True, rate, "bcv_scraping"
                                except Exception as e:
                                    log.debug(f"Could not parse rate from col-sm-6: {rate_str}, error: {e}")

                        # Strategy 2: Regex search for numbers in HTML (backup)
                        numbers = re.findall(r"\d+[.,]\d{2,}", html)
                        if numbers:
                            # Filter likely rates (3-4 digit numbers)
                            for num in numbers:
                                try:
                                    rate_str = num.replace(",", ".")
                                    rate = Decimal(rate_str)
                                    if 100 < rate < 1000:  # Reasonable BCV rate range
                                        log.info(f"✅ BCV scraping successful (regex): {rate}")
                                        return True, rate, "bcv_scraping"
                                except:
                                    continue

                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    log.debug(f"Timeout/Connection error with User-Agent {user_agent}: {e}")
                    continue
                except Exception as e:
                    log.debug(f"Error with User-Agent {user_agent}: {e}")
                    continue

            log.warning("❌ All BCV scraping strategies failed")
            return False, None, "All scraping strategies failed"

        except Exception as e:
            log.error(f"Unexpected error scraping BCV: {e}")
            return False, None, f"Scraping error: {str(e)}"

    @staticmethod
    async def fetch_from_fallback_api() -> tuple[bool, Decimal | None, str]:
        """
        Get rate from backup API (exchangerate-api.com free tier).
        Returns (success, rate, source_or_error_message)
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.exchangerate-api.com/v4/latest/USD",
                    headers={"User-Agent": "JADSlink/1.0"},
                )
                response.raise_for_status()

                data = response.json()

                # Look for VES (Bolívar Soberano - current) or VEF (old)
                rate_ves = data.get("rates", {}).get("VES")
                rate_vef = data.get("rates", {}).get("VEF")

                rate = rate_ves or rate_vef

                if rate:
                    rate = Decimal(str(rate))
                    log.info(f"Fallback API successful: {rate}")
                    return True, rate, "api_fallback"

                log.warning("VES/VEF rate not found in API response")
                return False, None, "Rate not found in API"

        except httpx.TimeoutException:
            log.error("Fallback API timeout (15 seconds)")
            return False, None, "API timeout"
        except httpx.HTTPError as e:
            log.error(f"HTTP error fetching from fallback API: {e}")
            return False, None, f"HTTP error: {str(e)}"
        except Exception as e:
            log.error(f"Unexpected error with fallback API: {e}")
            return False, None, f"API error: {str(e)}"

    @staticmethod
    async def get_current_rate(db: AsyncSession) -> Decimal:
        """
        Get the current active exchange rate from database.
        Falls back to hardcoded 36.50 if no rate found.
        """
        try:
            result = await db.execute(
                select(ExchangeRate)
                .where(ExchangeRate.is_active == True)
                .order_by(ExchangeRate.created_at.desc())
                .limit(1)
            )
            rate_record = result.scalar_one_or_none()

            if rate_record:
                return rate_record.rate

            log.warning("No active exchange rate found in database, using fallback 36.50")
            return Decimal("36.50")

        except Exception as e:
            log.error(f"Error retrieving current rate: {e}")
            return Decimal("36.50")

    @staticmethod
    async def set_manual_rate(
        db: AsyncSession,
        rate: Decimal,
        admin_email: str | None = None,
        notes: str | None = None,
    ) -> ExchangeRate:
        """
        Admin sets a new exchange rate manually.
        Deactivates all previous rates.

        Returns: ExchangeRate created
        """
        try:
            # Deactivate all previous rates
            await db.execute(update(ExchangeRate).values(is_active=False))

            # Create new active rate
            new_rate = ExchangeRate(
                rate=rate,
                source="manual",
                is_active=True,
                updated_by=admin_email,
                notes=notes or f"Manual update{f' by {admin_email}' if admin_email else ''}",
            )

            db.add(new_rate)
            await db.flush()

            log.info(f"Manual exchange rate set to {rate}{f' by {admin_email}' if admin_email else ''}")
            return new_rate

        except Exception as e:
            log.error(f"Error setting manual rate: {e}")
            raise

    @staticmethod
    async def update_rate(
        db: AsyncSession,
        api_key: str | None = None,
    ) -> tuple[bool, str]:
        """
        Update exchange rate using scraping + fallback strategy.
        Tries BCV scraping first, then falls back to API.

        Returns: (success, message)
        """
        # Try BCV scraping
        success, rate, source = await ExchangeRateService.scrape_bcv_rate()

        # If scraping fails, try fallback API
        if not success:
            log.warning("BCV scraping failed, trying fallback API")
            success, rate, source = await ExchangeRateService.fetch_from_fallback_api()

        # If both fail, use last known rate
        if not success:
            current_rate = await ExchangeRateService.get_current_rate(db)
            log.warning(f"Both scraping and API failed, keeping current rate: {current_rate}")
            message = f"Rate fetch failed ({source}), keeping previous rate: {current_rate}"
            return True, message

        try:
            # Deactivate previous rates
            await db.execute(update(ExchangeRate).values(is_active=False))

            # Create new rate
            new_rate = ExchangeRate(
                rate=rate,
                source=source,
                source_url="https://www.bcv.org.ve/" if source == "bcv_scraping" else "https://api.exchangerate-api.com/v4/latest/USD",
                is_active=True,
                updated_by="system",
                notes=f"Updated from {source}",
            )

            db.add(new_rate)
            await db.flush()

            message = f"Rate updated to {rate} ({source})"
            log.info(message)
            return True, message

        except Exception as e:
            log.error(f"Error saving rate: {e}")
            return False, f"Error saving rate: {str(e)}"

    @staticmethod
    async def get_rate_history(
        db: AsyncSession,
        limit: int = 30,
    ) -> list[ExchangeRate]:
        """
        Get exchange rate history (most recent first).
        """
        try:
            result = await db.execute(
                select(ExchangeRate)
                .order_by(ExchangeRate.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            log.error(f"Error retrieving rate history: {e}")
            return []
