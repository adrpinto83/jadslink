"""
Geolocation service using free IP-based geolocation API.
Uses ip-api.com (free tier, no API key required).
"""

import httpx
import logging
from typing import Optional
from datetime import datetime, timedelta

log = logging.getLogger("jadslink.geolocation")

# ip-api.com free API endpoint
GEOLOCATION_API = "http://ip-api.com/json"

# Simple in-memory cache for geolocation results
_location_cache: dict = {}
CACHE_TTL = timedelta(hours=24)


async def get_location_from_ip(ip_address: str) -> Optional[dict]:
    """
    Get location data from an IP address using ip-api.com.
    Includes caching and exponential backoff retry logic.

    Args:
        ip_address: IPv4 or IPv6 address

    Returns:
        Dictionary with location data or None if request fails
        {
            "lat": float,
            "lng": float,
            "address": str (city, region, country),
            "city": str,
            "region": str,
            "country": str,
            "timezone": str
        }
    """
    # Check cache first
    if ip_address in _location_cache:
        cached_data, timestamp = _location_cache[ip_address]
        if datetime.now() - timestamp < CACHE_TTL:
            log.debug(f"Cache hit for IP {ip_address}")
            return cached_data

    # Remove expired cache entry
    if ip_address in _location_cache:
        del _location_cache[ip_address]

    # Try to fetch with exponential backoff
    max_retries = 3
    base_timeout = 10  # Start with 10 second timeout

    for attempt in range(max_retries):
        try:
            timeout = base_timeout + (attempt * 5)  # 10s, 15s, 20s

            params = {
                "query": ip_address,
                "fields": "lat,lon,city,regionName,country,timezone,status"
            }

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(GEOLOCATION_API, params=params)
                response.raise_for_status()
                data = response.json()

                # Check if request was successful
                if data.get("status") != "success":
                    log.warning(f"Geolocation API returned error for IP {ip_address}: {data.get('message')}")
                    return None

                # Format response
                city = data.get("city", "")
                region = data.get("regionName", "")
                country = data.get("country", "")

                # Build address string
                address_parts = [part for part in [city, region, country] if part]
                address = ", ".join(address_parts) if address_parts else "Unknown Location"

                result = {
                    "lat": data.get("lat"),
                    "lng": data.get("lon"),  # Note: API uses 'lon', we use 'lng'
                    "address": address,
                    "city": city,
                    "region": region,
                    "country": country,
                    "timezone": data.get("timezone"),
                }

                # Cache successful result
                _location_cache[ip_address] = (result, datetime.now())
                log.info(f"Geolocation successful for IP {ip_address}: {address}")
                return result

        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                log.warning(f"Timeout getting location for IP {ip_address} (attempt {attempt + 1}/{max_retries}), retrying with longer timeout...")
                continue
            else:
                log.error(f"Timeout getting location for IP {ip_address} after {max_retries} attempts")
                return None

        except httpx.HTTPError as e:
            log.error(f"HTTP error getting location for IP {ip_address}: {e}")
            return None

        except Exception as e:
            log.error(f"Unexpected error in geolocation for IP {ip_address}: {e}")
            return None

    return None
