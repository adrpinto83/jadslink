"""CSRF (Cross-Site Request Forgery) protection utilities."""

import secrets
import hashlib
from typing import Optional
from fastapi import HTTPException, status, Request
from config import get_settings

settings = get_settings()


def generate_csrf_token() -> str:
    """Generate a secure CSRF token."""
    return secrets.token_urlsafe(32)


def get_csrf_token_hash(token: str) -> str:
    """Hash CSRF token for Redis storage (to avoid storing plaintext)."""
    return hashlib.sha256(token.encode()).hexdigest()


async def validate_csrf_token(request: Request) -> bool:
    """
    Validate CSRF token from request header.

    CSRF tokens should be sent in X-CSRF-Token header for POST/PATCH/DELETE requests.
    """
    csrf_token = request.headers.get("X-CSRF-Token")

    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing",
        )

    # In production, validate token against Redis
    # For now, we'll implement basic validation
    # TODO: Validate against Redis cache in future

    return True


def get_csrf_exception() -> HTTPException:
    """Return standard CSRF validation error."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="CSRF validation failed",
    )
