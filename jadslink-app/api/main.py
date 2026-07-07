from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os, asyncio, logging
from datetime import datetime, timedelta

from . import database
from .database import SessionLocal, DATA_DIR
from .models import Base, Device, Settings, Report, Client
from .routes import devices, codes, auth, portal, accounts, payments, shop, exchange
from .routes import settings as settings_route
from .routes.auth import hash_pw, ADMIN_PASSWORD
from .routes.devices import seed_devices
from .migrate import run_schema_migrations, run_data_migrations
from . import billing
from . import emailer

log = logging.getLogger("jadslink")

# Tracks devices already alerted so we don't spam
_alerted: set = set()

REPORT_RETENTION_DAYS = int(os.getenv("REPORT_RETENTION_DAYS", "30"))
CLIENT_RETENTION_DAYS = int(os.getenv("CLIENT_RETENTION_DAYS", "90"))


async def offline_alert_loop() -> None:
    await asyncio.sleep(30)  # wait for first heartbeat before checking
    while True:
        try:
            db = SessionLocal()
            try:
                if emailer.alerts_enabled(db):
                    thr_row = db.query(Settings).filter(Settings.key == "alert_threshold_min").first()
                    threshold = int(thr_row.value) if thr_row else 5
                    to_email = emailer.get_alert_recipient(db)

                    if to_email:
                        cutoff = datetime.utcnow() - timedelta(minutes=threshold)
                        all_devices = db.query(Device).all()
                        for d in all_devices:
                            is_offline = not d.last_seen or d.last_seen < cutoff
                            if is_offline and d.id not in _alerted:
                                when = d.last_seen.strftime("%H:%M UTC") if d.last_seen else "desconocido"
                                emailer.send_email(
                                    f"[JADSLink] Gateway offline: {d.name}",
                                    f"El gateway «{d.name}» no envía heartbeat desde las {when}.\n\n"
                                    f"Revisa el panel para más detalles:\nhttps://link.jadsstudio.com\n\n"
                                    f"— JADSLink Cloud",
                                    to_email,
                                )
                                _alerted.add(d.id)
                            elif not is_offline:
                                _alerted.discard(d.id)
            finally:
                db.close()
        except Exception:
            log.exception("offline_alert_loop")
        await asyncio.sleep(300)  # check every 5 minutes


async def billing_cycle_loop() -> None:
    """Marca cuentas vencidas como past_due/suspended (con periodo de gracia)."""
    await asyncio.sleep(60)  # esperar a que arranque
    while True:
        try:
            db = SessionLocal()
            try:
                billing.run_billing_cycle(db)
            finally:
                db.close()
        except Exception:
            log.exception("billing_cycle_loop")
        await asyncio.sleep(6 * 3600)  # revisar cada 6 horas


async def retention_loop() -> None:
    """Poda datos históricos para que la BD no crezca sin límite:
    - reports (un snapshot por heartbeat) más viejos que REPORT_RETENTION_DAYS
    - clients inactivos desconectados hace más de CLIENT_RETENTION_DAYS
    """
    await asyncio.sleep(120)
    while True:
        try:
            db = SessionLocal()
            try:
                now = datetime.utcnow()
                db.query(Report).filter(
                    Report.timestamp < now - timedelta(days=REPORT_RETENTION_DAYS)
                ).delete(synchronize_session=False)
                db.query(Client).filter(
                    Client.active == False,
                    Client.disconnected_at.isnot(None),
                    Client.disconnected_at < now - timedelta(days=CLIENT_RETENTION_DAYS),
                ).delete(synchronize_session=False)
                db.commit()
            finally:
                db.close()
        except Exception:
            log.exception("retention_loop")
        await asyncio.sleep(6 * 3600)


def _acquire_loop_lock():
    """Lock de instancia única para los loops de fondo: si algún día corren
    varios workers, solo uno envía alertas/factura/poda (evita duplicados)."""
    try:
        import fcntl
        f = open(os.path.join(DATA_DIR, "loops.lock"), "w")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except (OSError, ImportError):
        return None


def _startup_checks() -> None:
    """Advertencias de configuración insegura (no bloquean el arranque)."""
    if ADMIN_PASSWORD == "admin123":
        log.warning("ADMIN_PASSWORD no está configurado: el seed inicial usa 'admin123'. "
                    "Cambia la contraseña del superadmin desde el panel o define ADMIN_PASSWORD.")
    if not os.getenv("JWT_SECRET"):
        log.info("JWT_SECRET no definido: usando secreto autogenerado en %s/jwt_secret", DATA_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _startup_checks()
    Base.metadata.create_all(bind=database.engine)
    run_schema_migrations(database.engine)   # ALTER TABLE en tablas preexistentes (devices.account_id, etc.)
    db = SessionLocal()
    seed_devices(db)                # asegura routers conocidos
    run_data_migrations(db, ADMIN_PASSWORD, hash_pw)  # cuenta por defecto, superadmin, backfill
    db.close()
    tasks = []
    lock = _acquire_loop_lock()
    if lock is not None:
        tasks = [asyncio.create_task(offline_alert_loop()),
                 asyncio.create_task(billing_cycle_loop()),
                 asyncio.create_task(retention_loop())]
    yield
    for t in tasks:
        t.cancel()
    for t in tasks:
        try:
            await t
        except asyncio.CancelledError:
            pass
    if lock is not None:
        lock.close()


app = FastAPI(
    title="Hotspot Cloud Manager",
    description="API para gestión remota de dispositivos hotspot OpenWrt",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(payments.router)
app.include_router(devices.router)
app.include_router(codes.router)
app.include_router(settings_route.router)
app.include_router(portal.router)
app.include_router(shop.router)
app.include_router(exchange.router)

# Servir frontend estático
FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(os.path.join(FRONTEND, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND, "static")), name="static")

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND, "index.html"))

@app.get("/health")
def health():
    return {"status": "ok"}
