from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib, secrets, os

from ..database import get_db
from ..models import AdminUser

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TOKENS: dict[str, str] = {}   # token → username (en producción usar Redis/JWT)


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


class LoginPayload(BaseModel):
    username: str
    password: str


class ChangePasswordPayload(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    if not user or user.password_hash != hash_pw(payload.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = secrets.token_urlsafe(32)
    TOKENS[token] = payload.username
    return {"token": token, "username": payload.username}


@router.post("/logout")
def logout(token: str):
    TOKENS.pop(token, None)
    return {"ok": True}


@router.put("/password")
def change_password(
    payload: ChangePasswordPayload,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    raw_token = authorization.replace("Bearer ", "").strip()
    username = get_admin(raw_token)
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user or user.password_hash != hash_pw(payload.current_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mínimo 6 caracteres")
    user.password_hash = hash_pw(payload.new_password)
    db.commit()
    # Invalidar todas las sesiones del usuario
    for t in [t for t, u in TOKENS.items() if u == username]:
        TOKENS.pop(t, None)
    return {"ok": True}


def get_admin(token: str = "") -> str:
    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="No autenticado")
    return TOKENS[token]


def require_admin(authorization: str = Header(default="")) -> str:
    raw = authorization.replace("Bearer ", "").strip()
    return get_admin(raw)


def seed_admin(db: Session):
    admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if admin is None:
        db.add(AdminUser(username="admin", password_hash=hash_pw(ADMIN_PASSWORD)))
        db.commit()
    elif ADMIN_PASSWORD != "admin123" and admin.password_hash == hash_pw("admin123"):
        admin.password_hash = hash_pw(ADMIN_PASSWORD)
        db.commit()
