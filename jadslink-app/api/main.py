from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from .database import engine, SessionLocal
from .models import Base
from .routes import devices, codes, auth
from .routes.auth import seed_admin
from .routes.devices import seed_devices


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_admin(db)
    seed_devices(db)
    db.close()
    yield


app = FastAPI(
    title="Hotspot Cloud Manager",
    description="API para gestión remota de dispositivos hotspot OpenWrt",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(codes.router)

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
