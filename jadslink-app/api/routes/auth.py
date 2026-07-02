from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib, hmac, base64, json, time, os, secrets

from ..database import get_db, DATA_DIR
from ..models import User
from .. import ratelimit

router = APIRouter(prefix="/api/auth", tags=["auth"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TOKEN_TTL = int(os.getenv("TOKEN_TTL_DAYS", "7")) * 86400

PBKDF2_ITERATIONS = 200_000


def _load_secret() -> str:
    """Secreto para firmar tokens. Si no viene por env, genera uno aleatorio y
    lo persiste en el data dir para que las sesiones sobrevivan reinicios."""
    s = os.getenv("JWT_SECRET", "")
    if s and s != "change-me-in-production":
        return s
    path = os.path.join(DATA_DIR, "jwt_secret")
    try:
        if os.path.isfile(path):
            with open(path) as f:
                stored = f.read().strip()
            if stored:
                return stored
        generated = secrets.token_urlsafe(48)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(generated)
        return generated
    except OSError:
        # Sin disco escribible: secreto efímero (las sesiones mueren al reiniciar).
        return secrets.token_urlsafe(48)


SECRET = _load_secret()


# ── Hashing de contraseñas ─────────────────────────────────────────────────────
# Formato nuevo: pbkdf2$<iteraciones>$<salt_hex>$<hash_hex>
# Formato legacy: sha256 sin salt (BDs previas) — se verifica y se re-hashea al
# siguiente login exitoso.

def hash_pw(pw: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt}${dk.hex()}"


def verify_pw(pw: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("pbkdf2$"):
        try:
            _, iters, salt, hexhash = stored.split("$")
            dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(iters))
            return hmac.compare_digest(dk.hex(), hexhash)
        except (ValueError, TypeError):
            return False
    # legacy: sha256 plano
    return hmac.compare_digest(hashlib.sha256(pw.encode()).hexdigest(), stored)


def needs_rehash(stored: str) -> bool:
    return not stored.startswith("pbkdf2$")


def _pw_fingerprint(password_hash: str) -> str:
    """Fragmento derivado del hash actual: cambiar la contraseña invalida los
    tokens emitidos antes del cambio."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:12]


def _make_token(user: User) -> str:
    now = int(time.time())
    data = {
        "uid": user.id,
        "u": user.username,
        "aid": user.account_id or "",
        "r": user.role,
        "t": now,
        "exp": now + TOKEN_TTL,
        "ph": _pw_fingerprint(user.password_hash),
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
        if time.time() > data.get("exp", 0):
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
def login(payload: LoginPayload, request: Request, db: Session = Depends(get_db)):
    ip = ratelimit.client_ip(request)
    uname = payload.username.strip()
    ratelimit.check(f"login:ip:{ip}", limit=30, window_sec=60)
    if ratelimit.over_limit(f"login:fail:{ip}:{uname.lower()}", limit=5, window_sec=300):
        raise HTTPException(status_code=429, detail="Demasiados intentos fallidos. Espera 5 minutos.")

    user = db.query(User).filter(User.username == uname).first()
    if not user or not verify_pw(payload.password, user.password_hash) or not user.is_active:
        ratelimit.record(f"login:fail:{ip}:{uname.lower()}")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # Migración transparente de hashes legacy (sha256) a pbkdf2.
    if needs_rehash(user.password_hash):
        user.password_hash = hash_pw(payload.password)
        db.commit()

    return {
        "token": _make_token(user),
        "username": user.username,
        "role": user.role,
        "account_id": user.account_id or "",
    }


@router.post("/logout")
def logout():
    return {"ok": True}


# ── Dependencias de autenticación ──────────────────────────────────────────────

def get_current_user(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    token = authorization.replace("Bearer ", "").strip()
    data = _decode_token(token)
    user = db.query(User).filter(User.id == data.get("uid")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no válido")
    # El token queda inválido si la contraseña cambió después de emitirlo.
    if data.get("ph") != _pw_fingerprint(user.password_hash):
        raise HTTPException(status_code=401, detail="Sesión expirada")
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
    if not verify_pw(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Mínimo 8 caracteres")
    user.password_hash = hash_pw(payload.new_password)
    db.commit()
    # Al cambiar el hash, todos los tokens previos quedan inválidos (ph).
    return {"ok": True, "token": _make_token(user)}
