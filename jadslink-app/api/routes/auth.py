from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib, hmac, base64, json, time, os

from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TOKEN_TTL = 30 * 86400  # 30 días


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _make_token(user: User) -> str:
    data = {
        "uid": user.id,
        "u": user.username,
        "aid": user.account_id or "",
        "r": user.role,
        "t": int(time.time()),
    }
    payload = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET.encode(), payload.encode(), "sha256").hexdigest()
    return f"{payload}.{sig}"


def _decode_token(token: str) -> dict:
    try:
        payload, sig = token.rsplit(".", 1)
        expected = hmac.new(SECRET.encode(), payload.encode(), "sha256").hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=401, detail="Token inválido")
        data = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if time.time() - data["t"] > TOKEN_TTL:
            raise HTTPException(status_code=401, detail="Sesión expirada")
        return data
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
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or user.password_hash != hash_pw(payload.password) or not user.is_active:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return {
        "token": _make_token(user),
        "username": user.username,
        "role": user.role,
        "account_id": user.account_id or "",
    }


@router.post("/logout")
def logout(token: str = ""):
    return {"ok": True}


# ── Dependencias de autenticación ──────────────────────────────────────────────

def _raw_token(authorization: str, token: str) -> str:
    return authorization.replace("Bearer ", "").strip() or token.strip()


def get_current_user(
    authorization: str = Header(default=""),
    token: str = Query(default=""),
    db: Session = Depends(get_db),
) -> User:
    data = _decode_token(_raw_token(authorization, token))
    user = db.query(User).filter(User.id == data.get("uid")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no válido")
    return user


def require_user(user: User = Depends(get_current_user)) -> User:
    """Cualquier usuario autenticado activo."""
    return user


def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Requiere superadmin")
    return user


def require_manage(user: User = Depends(get_current_user)) -> User:
    """Puede gestionar routers/códigos/grupos: superadmin, owner o manager (no viewer)."""
    if user.role not in ("superadmin", "owner", "manager"):
        raise HTTPException(status_code=403, detail="Tu rol es de solo lectura")
    return user


def require_owner(user: User = Depends(get_current_user)) -> User:
    """Acciones de dueño (facturación, cuenta, usuarios): superadmin u owner."""
    if user.role not in ("superadmin", "owner"):
        raise HTTPException(status_code=403, detail="Requiere permisos de dueño de la cuenta")
    return user


@router.get("/me")
def me(user: User = Depends(require_user), db: Session = Depends(get_db)):
    from .. import billing
    account = user.account
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "account_id": user.account_id or "",
        "account": {
            "id": account.id, "name": account.name, "slug": account.slug,
            "status": account.status, "plan": account.plan,
            "usage": billing.compute_usage(db, account),
            "billing": billing.billing_info(account),
        } if account else None,
    }


@router.put("/password")
def change_password(
    payload: ChangePasswordPayload,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if user.password_hash != hash_pw(payload.current_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mínimo 6 caracteres")
    user.password_hash = hash_pw(payload.new_password)
    db.commit()
    return {"ok": True}
