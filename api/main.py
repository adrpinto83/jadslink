from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import get_settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import redis.asyncio as redis
import logging

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
        from services.session_service import expire_sessions

        async with async_session_maker() as db:
            await expire_sessions(db)

    scheduler.add_job(expire_sessions_job, "interval", seconds=60, id="expire_sessions")
    scheduler.start()
    app.state.scheduler = scheduler
    log.info("✓ APScheduler iniciado")

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
    }


from routers import auth, nodes, plans, tickets, portal, agent

app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Auth"])
app.include_router(nodes.router, prefix=f"{settings.API_PREFIX}/nodes", tags=["Nodes"])
app.include_router(plans.router, prefix=f"{settings.API_PREFIX}/plans", tags=["Plans"])
app.include_router(tickets.router, prefix=f"{settings.API_PREFIX}/tickets", tags=["Tickets"])
app.include_router(portal.router, prefix=f"{settings.API_PREFIX}/portal", tags=["Portal"])
app.include_router(agent.router, prefix=f"{settings.API_PREFIX}/agent", tags=["Agent"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development"
    )
