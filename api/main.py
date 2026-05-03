from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from config import get_settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from middleware.csrf import CSRFMiddleware
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
        try:
            from database import async_session_maker
            from services.session_service import SessionService

            async with async_session_maker() as db:
                service = SessionService(db)
                await service.expire_sessions()
                log.debug("✓ Sesiones expiradas")
        except Exception as e:
            log.error(f"Error en expire_sessions_job: {e}")

    def backup_database_job():
        """Periodic job to back up the database (MySQL or PostgreSQL)."""
        try:
            log.info("Iniciando backup de la base de datos...")
            backup_dir = Path("./backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_file = backup_dir / f"jadslink_backup_{timestamp}.sql"

            # Determine database type and construct appropriate backup command
            if "mysql" in settings.DATABASE_URL or "aiomysql" in settings.DATABASE_URL:
                # MySQL/MariaDB backup command
                try:
                    # Parse MySQL connection string: mysql+aiomysql://user:pass@host:port/dbname
                    db_url_parts = settings.DATABASE_URL.replace("mysql+aiomysql://", "").replace("+asyncpg", "")
                    user_pass, rest = db_url_parts.split("@")
                    user, password = user_pass.split(":")
                    host_port, dbname = rest.split("/")
                    host = host_port.split(":")[0]

                    command = [
                        "mysqldump",
                        f"--user={user}",
                        f"--password={password}",
                        f"--host={host}",
                        dbname,
                    ]
                    log.debug(f"Backup command: mysqldump (MySQL)")
                except Exception as parse_error:
                    log.warning(f"No se pudo parsear URL MySQL para backup, omitiendo: {parse_error}")
                    return

            else:
                # PostgreSQL backup command (legacy)
                db_url = settings.DATABASE_URL.replace("+asyncpg", "")
                command = [
                    "pg_dump",
                    db_url,
                ]
                log.debug("Backup command: pg_dump (PostgreSQL)")

            with open(dump_file, "w") as f:
                subprocess.run(
                    command,
                    stdout=f,
                    check=True,
                    text=True,
                    stderr=subprocess.DEVNULL,
                )

            # Gzip the backup file
            with gzip.open(str(dump_file) + ".gz", "wb") as f_out:
                with open(dump_file, "rb") as f_in:
                    f_out.writelines(f_in)

            # Remove the original sql file
            dump_file.unlink()

            log.info(f"✓ Backup de la base de datos completado con éxito: {dump_file}.gz")
        except subprocess.CalledProcessError as e:
            log.error(f"Error al hacer el backup de la base de datos: {e}")
        except Exception as e:
            log.error(f"Error inesperado en backup_database_job: {e}")

    async def check_offline_nodes_job():
        """Periodic job to check for offline nodes."""
        try:
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

                if offline_nodes:
                    for node in offline_nodes:
                        log.warning(f"NODO OFFLINE: {node.name} (ID: {node.id}) - Última vez visto: {node.last_seen_at}")
                    log.debug(f"✓ Verificación de nodos offline completada ({len(offline_nodes)} nodos offline)")
                else:
                    log.debug("✓ Todos los nodos online")
        except Exception as e:
            log.error(f"Error en check_offline_nodes_job: {e}")

    async def update_exchange_rate_job():
        """Periodic job to update exchange rate from BCV."""
        try:
            from database import async_session_maker
            from services.exchange_rate_service import ExchangeRateService

            log.debug("Running exchange rate update job...")
            async with async_session_maker() as db:
                success, message = await ExchangeRateService.update_rate(db)
                await db.commit()
                if success:
                    log.info(f"✓ Tasa de cambio actualizada: {message}")
                else:
                    log.warning(f"⚠ Advertencia en actualización de tasa: {message}")
        except Exception as e:
            log.error(f"Error en update_exchange_rate_job: {e}")

    # Add scheduled jobs with error handling wrappers
    try:
        scheduler.add_job(expire_sessions_job, "interval", seconds=60, id="expire_sessions", max_instances=1)
        scheduler.add_job(backup_database_job, "cron", hour=3, minute=0, id="db_backup", max_instances=1)
        scheduler.add_job(check_offline_nodes_job, "interval", minutes=5, id="offline_check", max_instances=1)
        scheduler.add_job(update_exchange_rate_job, "cron", hour=9, minute=0, id="update_exchange_rate", max_instances=1)

        scheduler.start()
        app.state.scheduler = scheduler
        log.info("✓ APScheduler iniciado con 4 trabajos periódicos")
        log.debug("  - expire_sessions (cada 60s)")
        log.debug("  - db_backup (diario a las 3 AM)")
        log.debug("  - offline_check (cada 5 min)")
        log.debug("  - update_exchange_rate (diario a las 9 AM)")
    except Exception as e:
        log.error(f"Error al inicializar APScheduler: {e}")
        # Continue anyway - scheduler is optional
        app.state.scheduler = None

    yield

    # Shutdown
    try:
        if hasattr(app.state, "scheduler") and app.state.scheduler and app.state.scheduler.running:
            app.state.scheduler.shutdown()
            log.debug("✓ APScheduler detenido")
    except Exception as e:
        log.error(f"Error al detener scheduler: {e}")

    try:
        if hasattr(app.state, "redis") and app.state.redis:
            await app.state.redis.close()
            log.debug("✓ Redis desconectado")
    except Exception as e:
        log.error(f"Error al cerrar Redis: {e}")

    log.info("🛑 JADSlink API detenido correctamente")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="API de plataforma SaaS para comercializar acceso a internet satelital",
    lifespan=lifespan,
)

# CORS configuration - Dynamic based on environment
if settings.ENVIRONMENT == "development":
    # Allow localhost for development
    origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://192.168.0.201:3000",
        "http://192.168.0.201:8000",
    ]
else:
    # Allow specific production domains
    origins = [
        "https://wheat-pigeon-347024.hostingersite.com",
        "http://wheat-pigeon-347024.hostingersite.com",
    ]
    # Add custom domain if configured
    if settings.FRONTEND_URL:
        origins.append(settings.FRONTEND_URL)

log.debug(f"CORS allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF protection middleware
app.add_middleware(CSRFMiddleware)

# Add metrics middleware for Prometheus
# from utils.metrics import MetricsMiddleware
# app.add_middleware(MetricsMiddleware)


from routers import auth
from routers import nodes
from routers import plans
from routers import plans_saas
from routers import tickets
from routers import portal
from routers import agent
from routers import tenants
from routers import admin
from routers import subscriptions
from routers import upgrades
from routers import webhooks
from routers import health
from routers import sessions
from routers import pricing
from routers import utils
from routers import uploads

app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Auth"])
app.include_router(tenants.router, prefix=f"{settings.API_PREFIX}/tenants", tags=["Tenants"])
app.include_router(admin.router, prefix=f"{settings.API_PREFIX}/admin", tags=["Admin"])
app.include_router(pricing.router, prefix=f"{settings.API_PREFIX}/admin/pricing", tags=["Admin"])
app.include_router(subscriptions.router, prefix=f"{settings.API_PREFIX}/subscriptions", tags=["Subscriptions"])
app.include_router(upgrades.router, prefix=f"{settings.API_PREFIX}/subscriptions", tags=["Subscriptions"])
app.include_router(webhooks.router, prefix=f"{settings.API_PREFIX}/webhooks", tags=["Webhooks"])
app.include_router(nodes.router, prefix=f"{settings.API_PREFIX}/nodes", tags=["Nodes"])
app.include_router(plans.router, prefix=f"{settings.API_PREFIX}/plans", tags=["Plans"])
app.include_router(plans_saas.router, prefix=f"{settings.API_PREFIX}/saas-plans", tags=["SaaS Plans"])
app.include_router(tickets.router, prefix=f"{settings.API_PREFIX}/tickets", tags=["Tickets"])
app.include_router(sessions.router, prefix=f"{settings.API_PREFIX}/sessions", tags=["Sessions"])
app.include_router(portal.router, prefix=f"{settings.API_PREFIX}/portal", tags=["Portal"])
app.include_router(agent.router, prefix=f"{settings.API_PREFIX}/agent", tags=["Agent"])
app.include_router(uploads.router, prefix=f"{settings.API_PREFIX}/uploads", tags=["Uploads"])
app.include_router(utils.router, prefix=f"{settings.API_PREFIX}/utils", tags=["Utilities"])
app.include_router(health.router, tags=["Health & Monitoring"])

# Serve static files (logos, etc.)
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development"
    )
