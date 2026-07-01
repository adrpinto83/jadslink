from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib, hmac, base64, json, time, os

from ..database import get_db
from ..models import AdminUser

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TOKEN_TTL = 30 * 86400  # 30 días


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _make_token(username: str) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"u": username, "t": int(time.time())}).encode()
    ).decode().rstrip("=")
    sig = hmac.new(SECRET.encode(), payload.encode(), "sha256").hexdigest()
    return f"{payload}.{sig}"


def _verify_token(token: str) -> str:
    try:
        payload, sig = token.rsplit(".", 1)
        expected = hmac.new(SECRET.encode(), payload.encode(), "sha256").hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=401, detail="Token inválido")
        data = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if time.time() - data["t"] > TOKEN_TTL:
            raise HTTPException(status_code=401, detail="Sesión expirada")
        return data["u"]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


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
    return {"token": _make_token(payload.username), "username": payload.username}


@router.post("/logout")
def logout(token: str):
    return {"ok": True}


@router.put("/password")
def change_password(
    payload: ChangePasswordPayload,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    raw_token = authorization.replace("Bearer ", "").strip()
    username = _verify_token(raw_token)
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user or user.password_hash != hash_pw(payload.current_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mínimo 6 caracteres")
    user.password_hash = hash_pw(payload.new_password)
    db.commit()
    return {"ok": True}


def get_admin(token: str = "") -> str:
    return _verify_token(token)


def require_admin(
    authorization: str = Header(default=""),
    token: str = Query(default=""),
) -> str:
    raw = authorization.replace("Bearer ", "").strip() or token.strip()
    return get_admin(raw)


def seed_admin(db: Session):
    admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    if admin is None:
        db.add(AdminUser(username="admin", password_hash=hash_pw(ADMIN_PASSWORD)))
        db.commit()
    elif ADMIN_PASSWORD != "admin123" and admin.password_hash == hash_pw("admin123"):
        admin.password_hash = hash_pw(ADMIN_PASSWORD)
        db.commit()
