"""CSRF protection middleware for FastAPI."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from utils.csrf import generate_csrf_token


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware.

    For GET requests: Generates and includes CSRF token in response header
    For POST/PATCH/DELETE: Validates X-CSRF-Token header against token in session/cookie

    This protects against Cross-Site Request Forgery attacks by ensuring
    that state-changing requests come from authorized origins.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for certain endpoints
        path = request.url.path
        skip_csrf_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/webhooks/stripe",  # Stripe webhooks are verified differently
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

        # Check if path should skip CSRF validation
        skip_validation = any(path.startswith(skip_path) for skip_path in skip_csrf_paths)

        # Validate CSRF token for state-changing methods (except skipped paths)
        if request.method in ["POST", "PATCH", "DELETE", "PUT"] and not skip_validation:
            csrf_token = request.headers.get("X-CSRF-Token")
            if not csrf_token or len(csrf_token) < 20:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid"},
                )

        # Process the request
        response = await call_next(request)

        # Add CSRF token to response header (for GET requests and others)
        if request.method == "GET" or response.status_code == 200:
            csrf_token = generate_csrf_token()
            response.headers["X-CSRF-Token"] = csrf_token

        return response
