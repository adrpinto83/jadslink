"""Gestión de cuentas (tenants), sus usuarios y grupos de routers.

- Superadmin: crea/lista/edita cualquier cuenta y usuario.
- Owner: gestiona su propia cuenta, sus usuarios (manager/viewer) y sus grupos.
"""
import uuid, re
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Account, User, DeviceGroup, Device, SubscriptionPlan, TicketQuotaLog
from .auth import require_user, require_superadmin, require_manage, hash_pw, _make_token
from ..scope import is_superadmin
from .. import billing, ratelimit, quota

router = APIRouter(prefix="/api", tags=["accounts"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    name: str
    plan: str = "trial"
    contact_phone: str = ""
    # Owner inicial de la cuenta (login del operador)
    owner_username: str
    owner_password: str
    owner_email: str = ""

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None
    contact_phone: Optional[str] = None
    payment_methods: Optional[dict] = None   # datos de cobro para la venta online

class SignupPayload(BaseModel):
    company_name: str
    username: str
    password: str
    email: str = ""
    contact_phone: str = ""

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = ""
    email: str = ""
    role: str = "manager"     # owner|manager|viewer

class GroupCreate(BaseModel):
    name: str
    account_id: Optional[str] = None   # solo superadmin

class GroupUpdate(BaseModel):
    name: str


class GrantTicketsPayload(BaseModel):
    quantity: int
    note: str = ""


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "cuenta"
    return base


def _unique_slug(db: Session, name: str) -> str:
    base = _slugify(name)
    slug, i = base, 2
    while db.query(Account).filter(Account.slug == slug).first():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _account_dict(a: Account, db: Session) -> dict:
    usage = billing.compute_usage(db, a)
    quota_info = quota.get_quota_info(db, a)
    has_superadmin = db.query(User).filter(
        User.account_id == a.id,
        User.role == "superadmin"
    ).first() is not None
    
    return {
        "id": a.id, "name": a.name, "slug": a.slug,
        "status": a.status, "plan": a.plan,
        "contact_phone": a.contact_phone,
        "payment_methods": a.payment_methods or {},
        "device_count": usage["device_count"],
        "usage": usage,
        "quota": quota_info,
        "billing": billing.billing_info(a),
        "billing_cycle_end": a.billing_cycle_end.isoformat() if a.billing_cycle_end else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "deleted_at": a.deleted_at.isoformat() if a.deleted_at else None,
        "has_superadmin": has_superadmin,
    }

@router.get("/plans")
def list_plans(db: Session = Depends(get_db), _: User = Depends(require_user)):
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True)\
              .order_by(SubscriptionPlan.sort_order.asc()).all()
    return [{
        "key": p.key, "name": p.name, "base_price_usd": p.base_price_usd,
        "included_devices": p.included_devices,
        "price_per_extra_device_usd": p.price_per_extra_device_usd,
        "max_devices": p.max_devices, "features": p.features,
    } for p in plans]


# ── Cuentas ────────────────────────────────────────────────────────────────────

@router.get("/accounts")
def list_accounts(include_deleted: bool = False, db: Session = Depends(get_db), _: User = Depends(require_superadmin)):
    q = db.query(Account)
    if not include_deleted:
        q = q.filter(Account.deleted_at.is_(None))
    return [_account_dict(a, db) for a in q.order_by(Account.created_at.desc()).all()]


@router.get("/admin/revenue")
def revenue(db: Session = Depends(get_db), _: User = Depends(require_superadmin)):
    """Resumen de ingresos para el superadmin: MRR estimado y estado de la cartera."""
    from ..models import Payment
    accs = db.query(Account).all()
    by_status: dict = {}
    mrr = 0.0
    devices = 0
    for a in accs:
        by_status[a.status] = by_status.get(a.status, 0) + 1
        u = billing.compute_usage(db, a)
        devices += u["device_count"]
        if a.status in ("active", "past_due"):  # cuentas que deberían estar pagando
            mrr += u["total_monthly"]
    return {
        "accounts_total": len(accs),
        "by_status": by_status,
        "mrr": round(mrr, 2),
        "devices_total": devices,
        "pending_payments": db.query(Payment).filter(Payment.status == "pending").count(),
    }


def create_account_with_owner(db: Session, *, name: str, plan: str, username: str,
                              password: str, email: str = "", contact_phone: str = "") -> Account:
    """Crea una cuenta + su usuario owner. Lanza HTTP 400 si el usuario ya existe."""
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    acc = Account(
        id=str(uuid.uuid4()),
        name=name,
        slug=_unique_slug(db, name),
        plan=plan,
        contact_phone=contact_phone,
    )
    billing.init_billing_for_new_account(acc, plan)  # fija vencimiento/trial y status
    db.add(acc)
    db.flush()  # obtener acc.id sin cerrar la transacción
    db.add(User(
        account_id=acc.id,
        username=username,
        password_hash=hash_pw(password),
        email=email,
        role="owner",
        full_name=name,
    ))
    db.commit()
    return acc


@router.post("/signup")
def signup(payload: SignupPayload, request: Request, db: Session = Depends(get_db)):
    """Registro público self-service → crea una cuenta trial y devuelve token (auto-login)."""
    # Endpoint público: rate limit para evitar creación masiva de cuentas trial.
    ratelimit.check(f"signup:{ratelimit.client_ip(request)}", limit=10, window_sec=3600)
    name = payload.company_name.strip()
    username = payload.username.strip()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Nombre de empresa inválido")
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="El usuario debe tener al menos 3 caracteres")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    # El registro público siempre arranca en trial; luego el owner puede elegir plan y pagar.
    acc = create_account_with_owner(
        db, name=name, plan="trial", username=username,
        password=payload.password, email=payload.email, contact_phone=payload.contact_phone,
    )
    user = db.query(User).filter(User.username == username).first()
    return {
        "token": _make_token(user),
        "username": user.username,
        "role": user.role,
        "account_id": user.account_id or "",
    }


@router.post("/accounts")
def create_account(payload: AccountCreate, db: Session = Depends(get_db), _: User = Depends(require_superadmin)):
    acc = create_account_with_owner(
        db, name=payload.name, plan=payload.plan, username=payload.owner_username,
        password=payload.owner_password, email=payload.owner_email, contact_phone=payload.contact_phone,
    )
    return _account_dict(acc, db)


@router.get("/accounts/{account_id}")
def get_account(account_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    if not is_superadmin(user) and user.account_id != account_id:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return _account_dict(acc, db)


@router.patch("/accounts/{account_id}")
def update_account(account_id: str, payload: AccountUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    own = is_superadmin(user) or (user.account_id == account_id and user.role == "owner")
    if not own:
        raise HTTPException(status_code=403, detail="Sin permiso")
    if payload.name is not None:
        acc.name = payload.name
    if payload.contact_phone is not None:
        acc.contact_phone = payload.contact_phone
    if payload.payment_methods is not None:
        # Solo métodos conocidos, valores de texto plano acotados
        from .shop import METHODS
        acc.payment_methods = {
            k: str(v).strip()[:300]
            for k, v in payload.payment_methods.items() if k in METHODS
        }
    # El owner puede elegir su propio plan (self-service); el pago se aprueba aparte.
    if payload.plan is not None:
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.key == payload.plan, SubscriptionPlan.is_active == True
        ).first()
        if not plan:
            raise HTTPException(status_code=400, detail="Plan inválido")
        acc.plan = payload.plan
    # El estado (activa/suspendida) solo lo cambia el superadmin.
    if is_superadmin(user) and payload.status is not None:
        acc.status = payload.status
    db.commit()
    return _account_dict(acc, db)


# ── Usuarios de una cuenta ──────────────────────────────────────────────────────

@router.get("/accounts/{account_id}/users")
def list_users(account_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    own = is_superadmin(user) or (user.account_id == account_id and user.role in ("owner", "manager"))
    if not own:
        raise HTTPException(status_code=403, detail="Sin permiso")
    users = db.query(User).filter(User.account_id == account_id).all()
    return [{
        "id": u.id, "username": u.username, "email": u.email,
        "full_name": u.full_name, "role": u.role, "is_active": u.is_active,
    } for u in users]


@router.post("/accounts/{account_id}/users")
def create_user(account_id: str, payload: UserCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    own = is_superadmin(user) or (user.account_id == account_id and user.role == "owner")
    if not own:
        raise HTTPException(status_code=403, detail="Sin permiso")
    if payload.role not in ("owner", "manager", "viewer"):
        raise HTTPException(status_code=400, detail="Rol inválido")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    u = User(
        account_id=account_id,
        username=payload.username,
        password_hash=hash_pw(payload.password),
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role,
    )
    db.add(u)
    db.commit()
    return {"id": u.id, "username": u.username, "role": u.role}


# ── Grupos de routers ────────────────────────────────────────────────────────────

def _group_account_id(payload_account_id: Optional[str], user: User) -> str:
    if is_superadmin(user):
        if not payload_account_id:
            raise HTTPException(status_code=400, detail="account_id requerido para superadmin")
        return payload_account_id
    return user.account_id


@router.get("/groups")
def list_groups(account_id: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(require_user)):
    if is_superadmin(user):
        q = db.query(DeviceGroup)
        if account_id:
            q = q.filter(DeviceGroup.account_id == account_id)
    else:
        q = db.query(DeviceGroup).filter(DeviceGroup.account_id == user.account_id)
    return [{"id": g.id, "name": g.name, "account_id": g.account_id,
             "device_count": db.query(Device).filter(Device.group_id == g.id).count()}
            for g in q.order_by(DeviceGroup.name.asc()).all()]


@router.post("/groups")
def create_group(payload: GroupCreate, db: Session = Depends(get_db), user: User = Depends(require_manage)):
    acc_id = _group_account_id(payload.account_id, user)
    g = DeviceGroup(account_id=acc_id, name=payload.name)
    db.add(g)
    db.commit()
    return {"id": g.id, "name": g.name, "account_id": g.account_id}


@router.patch("/groups/{group_id}")
def rename_group(group_id: int, payload: GroupUpdate, db: Session = Depends(get_db), user: User = Depends(require_manage)):
    g = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not g or (not is_superadmin(user) and g.account_id != user.account_id):
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    g.name = payload.name
    db.commit()
    return {"ok": True}


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db), user: User = Depends(require_manage)):
    g = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not g or (not is_superadmin(user) and g.account_id != user.account_id):
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    # Desasociar routers del grupo antes de borrarlo
    db.query(Device).filter(Device.group_id == group_id).update({"group_id": None})
    db.delete(g)
    db.commit()
    return {"ok": True}


# ── Soft delete y restauración de cuentas ────────────────────────────────────────

@router.delete("/accounts/{account_id}")
def delete_account(account_id: str, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    """Soft delete de una cuenta (solo superadmin)."""
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if acc.deleted_at is not None:
        raise HTTPException(status_code=400, detail="La cuenta ya está eliminada")
    
    # Prevenir eliminación de cuenta con usuarios superadmin
    has_superadmin = db.query(User).filter(
        User.account_id == account_id,
        User.role == "superadmin"
    ).first()
    if has_superadmin:
        raise HTTPException(status_code=403, detail="No se puede eliminar la cuenta del superadmin")

    from datetime import datetime
    acc.deleted_at = datetime.utcnow()
    acc.deleted_by = user.id
    db.commit()
    return {"ok": True, "message": f"Cuenta '{acc.name}' eliminada"}

@router.post("/accounts/{account_id}/restore")
def restore_account(account_id: str, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    """Restaurar una cuenta eliminada (solo superadmin)."""
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if acc.deleted_at is None:
        raise HTTPException(status_code=400, detail="La cuenta no está eliminada")

    acc.deleted_at = None
    acc.deleted_by = None
    db.commit()
    return {"ok": True, "message": f"Cuenta '{acc.name}' restaurada"}


# ── Gestión de cuotas de tickets ─────────────────────────────────────────────────

@router.get("/accounts/{account_id}/tickets/quota")
def get_account_quota(account_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Ver estado de cuota de tickets de una cuenta."""
    if not is_superadmin(user) and user.account_id != account_id:
        raise HTTPException(status_code=403, detail="Sin permiso")

    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    return quota.get_quota_info(db, acc)


@router.post("/accounts/{account_id}/tickets/grant")
def grant_tickets(account_id: str, payload: GrantTicketsPayload, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    """Otorgar tickets gratis a una cuenta (solo superadmin)."""
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if acc.deleted_at is not None:
        raise HTTPException(status_code=400, detail="No se pueden otorgar tickets a una cuenta eliminada")
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")

    quota.grant_bonus_tickets(db, acc, payload.quantity, user.id, payload.note)
    db.commit()

    return {
        "ok": True,
        "message": f"Se otorgaron {payload.quantity} tickets bonus a '{acc.name}'",
        "quota": quota.get_quota_info(db, acc),
    }


@router.get("/accounts/{account_id}/tickets/history")
def get_ticket_history(account_id: str, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Ver historial de uso/asignación de tickets de una cuenta."""
    if not is_superadmin(user) and user.account_id != account_id:
        raise HTTPException(status_code=403, detail="Sin permiso")

    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    logs = db.query(TicketQuotaLog).filter(
        TicketQuotaLog.account_id == account_id
    ).order_by(TicketQuotaLog.created_at.desc()).limit(limit).all()

    return [{
        "id": log.id,
        "action": log.action,
        "quantity": log.quantity,
        "note": log.note,
        "performed_by": log.performed_by,
        "created_at": log.created_at.isoformat(),
    } for log in logs]
