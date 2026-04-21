"""
Health check endpoints for monitoring and load balancers.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime, timezone, timedelta
import logging

from database import get_db
from models.node import Node
from utils.metrics import service_health, nodes_offline

log = logging.getLogger("jadslink.health")

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Basic health check endpoint.
    Returns 200 if service is healthy, 503 if not.
    """
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        db_health = True
    except Exception as e:
        log.error(f"Database health check failed: {e}")
        db_health = False

    service_health.labels(service="database").set(1 if db_health else 0)

    if not db_health:
        return {
            "status": "unhealthy",
            "checks": {"database": "failed"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, 503

    return {
        "status": "healthy",
        "checks": {"database": "ok"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check - returns 200 when service is ready to handle traffic.
    Used by load balancers for routing decisions.
    """
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        log.error(f"Readiness check failed: {e}")
        return {"ready": False}, 503


@router.get("/health/nodes")
async def nodes_health_check(db: AsyncSession = Depends(get_db)):
    """
    Check node health status.
    Returns count of online/offline/stale nodes.
    """
    now = datetime.now(timezone.utc)
    five_minutes_ago = now - timedelta(minutes=5)

    # Get all active nodes
    result = await db.execute(
        select(Node).where(Node.deleted_at == None)
    )
    nodes = result.scalars().all()

    online = 0
    offline = 0
    stale = 0

    for node in nodes:
        if node.last_seen_at is None:
            offline += 1
        elif node.last_seen_at < five_minutes_ago:
            stale += 1
        else:
            online += 1

    # Update metric
    nodes_offline.set(offline + stale)

    return {
        "timestamp": now.isoformat(),
        "nodes": {
            "total": len(nodes),
            "online": online,
            "stale": stale,  # Not seen in > 5 minutes
            "offline": offline,  # Never reported
        },
        "health": "healthy" if offline == 0 else "degraded",
    }


@router.get("/metrics")
async def prometheus_metrics():
    """
    Expose Prometheus metrics.
    This endpoint is scraped by Prometheus for monitoring.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response

    metrics_output = generate_latest()
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)
