"""Rate limiting utilities using Redis"""

from fastapi import Request, HTTPException, status
from typing import Callable
import logging

log = logging.getLogger("jadslink.rate_limit")


class RateLimiter:
    """Rate limiter using Redis backend"""

    def __init__(self, max_requests: int, window_seconds: int, key_prefix: str = "rate_limit"):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
            key_prefix: Redis key prefix for rate limit tracking
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier (IP address)"""
        if request.client:
            return request.client.host
        return "unknown"

    def _get_rate_limit_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"{self.key_prefix}:{endpoint}:{identifier}"

    async def check_rate_limit(self, request: Request, endpoint: str) -> None:
        """
        Check if request exceeds rate limit.

        Raises:
            HTTPException: If rate limit is exceeded
        """
        redis = getattr(request.app.state, "redis", None)
        if not redis:
            # Rate limiting disabled if Redis not available
            return

        client_id = self._get_client_identifier(request)
        rate_limit_key = self._get_rate_limit_key(client_id, endpoint)

        try:
            # Increment counter
            attempts = await redis.incr(rate_limit_key)

            # Set expiration on first request
            if attempts == 1:
                await redis.expire(rate_limit_key, self.window_seconds)

            # Check if limit exceeded
            if attempts > self.max_requests:
                log.warning(
                    f"Rate limit exceeded for {client_id} on {endpoint}: "
                    f"{attempts}/{self.max_requests} in {self.window_seconds}s"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Demasiadas solicitudes. Intenta de nuevo en {self.window_seconds} segundos.",
                )

        except HTTPException:
            raise
        except Exception as e:
            log.warning(f"Rate limiting error: {e}")
            # Continue without rate limiting if Redis fails


def rate_limit(max_requests: int = 10, window_seconds: int = 60, endpoint: str = "default"):
    """
    Dependency factory for rate limiting.

    Usage:
        @router.post("/endpoint")
        async def my_endpoint(
            request: Request,
            _: None = Depends(rate_limit(max_requests=5, window_seconds=60, endpoint="my_endpoint"))
        ):
            ...

    Args:
        max_requests: Maximum requests allowed in the window
        window_seconds: Time window in seconds
        endpoint: Endpoint identifier for rate limiting

    Returns:
        Dependency callable
    """
    limiter = RateLimiter(max_requests, window_seconds)

    async def rate_limit_dependency(request: Request) -> None:
        await limiter.check_rate_limit(request, endpoint)

    return rate_limit_dependency
