"""
Prometheus metrics for JADSlink API.

Exposes custom metrics via /metrics endpoint for monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram, Info
import time

# Application info
app_info = Info("jadslink_app", "JADSlink API information")

# Request metrics
request_count = Counter(
    "jadslink_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"],
)

request_duration = Histogram(
    "jadslink_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
)

# Database metrics
db_query_duration = Histogram(
    "jadslink_db_query_duration_seconds",
    "Database query duration",
    ["operation", "table"],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0),
)

db_connection_pool_size = Gauge(
    "jadslink_db_connection_pool_size",
    "Database connection pool size",
)

# Business metrics
active_sessions = Gauge(
    "jadslink_active_sessions_total",
    "Total number of active sessions",
)

tickets_generated_total = Counter(
    "jadslink_tickets_generated_total",
    "Total tickets generated",
    ["tenant_id", "plan_tier"],
)

nodes_total = Gauge(
    "jadslink_nodes_total",
    "Total number of nodes",
    ["status"],
)

nodes_offline = Gauge(
    "jadslink_nodes_offline_total",
    "Number of offline nodes",
)

# Stripe metrics
stripe_checkout_initiated = Counter(
    "jadslink_stripe_checkout_initiated_total",
    "Stripe checkout sessions created",
    ["plan"],
)

stripe_subscription_created = Counter(
    "jadslink_stripe_subscription_created_total",
    "Stripe subscriptions created",
    ["plan"],
)

stripe_webhook_received = Counter(
    "jadslink_stripe_webhook_received_total",
    "Stripe webhooks received",
    ["event_type", "status"],
)

# Error metrics
errors_total = Counter(
    "jadslink_errors_total",
    "Total number of errors",
    ["error_type", "endpoint"],
)

rate_limit_exceeded = Counter(
    "jadslink_rate_limit_exceeded_total",
    "Rate limit exceeded events",
    ["endpoint"],
)

# Health metrics
service_health = Gauge(
    "jadslink_service_health",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service"],
)


class MetricsMiddleware:
    """ASGI middleware for collecting metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        method = scope["method"]

        # Skip metrics endpoint to avoid recursion
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        # Normalize path (replace IDs with placeholder)
        normalized_path = self._normalize_path(path)

        start_time = time.time()
        status = 500

        async def send_with_metrics(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_with_metrics)
        except Exception as e:
            status = 500
            errors_total.labels(error_type=type(e).__name__, endpoint=normalized_path).inc()
            raise
        finally:
            duration = time.time() - start_time
            request_count.labels(
                method=method,
                endpoint=normalized_path,
                status=status,
            ).inc()
            request_duration.labels(
                method=method,
                endpoint=normalized_path,
            ).observe(duration)

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize path by replacing UUIDs with {id}."""
        import re
        # Replace UUID patterns with {id}
        return re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )
