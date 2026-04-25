from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import get_settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import redis.asyncio as redis
import logging

import subprocess
import gzip
from datetime import datetime
from pathlib import Path

# Setup structured logging first
from utils.logging_config import setup_logging
setup_logging()

settings = get_settings()
log = logging.getLogger("jadslink.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    log.info(f"🚀 JADSlink API iniciado | Ambiente: {settings.ENVIRONMENT}")

    # Initialize Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        app.state.redis = redis_client
        log.info("✓ Redis conectado")
    except Exception as e:
        log.warning(f"⚠ Redis no disponible: {e} (operando sin cache)")
        app.state.redis = None

    # Initialize APScheduler
    scheduler = AsyncIOScheduler()

    async def expire_sessions_job():
        """Periodic job to expire sessions"""
        from database import async_session_maker
        from services.session_service import SessionService

        async with async_session_maker() as db:
            service = SessionService(db)
            await service.expire_sessions()

    def backup_database_job():
        """Periodic job to back up the PostgreSQL database."""
        log.info("Iniciando backup de la base de datos...")
        backup_dir = Path("./backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create a temporary file for the SQL dump
        dump_file = backup_dir / f"jadslink_backup_{timestamp}.sql"

        # Construct the pg_dump command
        db_url = settings.DATABASE_URL.replace("+asyncpg", "") # pg_dump doesn't use asyncpg
        command = [
            "pg_dump",
            db_url,
        ]
        
        try:
            with open(dump_file, "w") as f:
                subprocess.run(
                    command,
                    stdout=f,
                    check=True,
                    text=True,
                )
            
            # Gzip the backup file
            with gzip.open(str(dump_file) + ".gz", "wb") as f_out:
                with open(dump_file, "rb") as f_in:
                    f_out.writelines(f_in)
            
            # Remove the original sql file
            dump_file.unlink()
            
            log.info(f"Backup de la base de datos completado con éxito: {dump_file}.gz")
        except subprocess.CalledProcessError as e:
            log.error(f"Error al hacer el backup de la base de datos: {e}")

    async def check_offline_nodes_job():
        """Periodic job to check for offline nodes."""
        from database import async_session_maker
        from sqlalchemy import select
        from models.node import Node
        from datetime import timedelta, timezone

        log.debug("Running offline node check...")
        async with async_session_maker() as db:
            five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
            result = await db.execute(
                select(Node).where(Node.last_seen_at < five_minutes_ago)
            )
            offline_nodes = result.scalars().all()

            for node in offline_nodes:
                log.warning(f"NODO OFFLINE: {node.name} (ID: {node.id}) - Última vez visto: {node.last_seen_at}")

    scheduler.add_job(expire_sessions_job, "interval", seconds=60, id="expire_sessions")
    scheduler.add_job(backup_database_job, "cron", hour=3, minute=0, id="db_backup") # Run daily at 3 AM
    scheduler.add_job(check_offline_nodes_job, "interval", minutes=5, id="offline_check")
    
    scheduler.start()
    app.state.scheduler = scheduler
    log.info("✓ APScheduler iniciado con trabajos de expiración y backup")

    yield

    # Shutdown
    if hasattr(app.state, "scheduler") and app.state.scheduler.running:
        app.state.scheduler.shutdown()
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
    log.info("🛑 JADSlink API detenido")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="API de plataforma SaaS para comercializar acceso a internet satelital",
    lifespan=lifespan,
)

# CORS configuration
origins = [
    "http://localhost:5173", # React frontend development server
    "http://localhost:5174", # Alternative port
    "http://localhost:3000",  # Common dev port
    # TODO: Add production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware for Prometheus
from utils.metrics import MetricsMiddleware
app.add_middleware(MetricsMiddleware)


from routers import auth
from routers import nodes
from routers import plans
from routers import tickets
from routers import portal
from routers import agent
from routers import tenants
from routers import admin
from routers import subscriptions
from routers import webhooks
from routers import health
from routers import sessions

app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Auth"])
app.include_router(tenants.router, prefix=f"{settings.API_PREFIX}/tenants", tags=["Tenants"])
app.include_router(admin.router, prefix=f"{settings.API_PREFIX}/admin", tags=["Admin"])
app.include_router(subscriptions.router, prefix=f"{settings.API_PREFIX}/subscriptions", tags=["Subscriptions"])
app.include_router(webhooks.router, prefix=f"{settings.API_PREFIX}/webhooks", tags=["Webhooks"])
app.include_router(nodes.router, prefix=f"{settings.API_PREFIX}/nodes", tags=["Nodes"])
app.include_router(plans.router, prefix=f"{settings.API_PREFIX}/plans", tags=["Plans"])
app.include_router(tickets.router, prefix=f"{settings.API_PREFIX}/tickets", tags=["Tickets"])
app.include_router(sessions.router, prefix=f"{settings.API_PREFIX}/sessions", tags=["Sessions"])
app.include_router(portal.router, prefix=f"{settings.API_PREFIX}/portal", tags=["Portal"])
app.include_router(agent.router, prefix=f"{settings.API_PREFIX}/agent", tags=["Agent"])
app.include_router(health.router, tags=["Health & Monitoring"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development"
    )
