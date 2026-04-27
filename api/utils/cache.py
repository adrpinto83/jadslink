"""Simple in-memory caching utility for frequently accessed data."""

from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import asyncio

class CacheEntry:
    """Container for cached value with TTL."""

    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """Set value in cache with TTL."""
        self._cache[key] = CacheEntry(value, ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, return None if expired or missing."""
        entry = self._cache.get(key)
        if not entry:
            return None

        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.value

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def get_or_compute(self, key: str, compute_fn: Callable, ttl_seconds: int = 60) -> Any:
        """Get from cache or compute and store value."""
        cached = self.get(key)
        if cached is not None:
            return cached

        value = compute_fn()
        self.set(key, value, ttl_seconds)
        return value


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get global cache instance."""
    return _cache
