"""Gestión de cuentas (tenants), sus usuarios y grupos de routers.

- Superadmin: crea/lista/edita cualquier cuenta y usuario.
- Owner: gestiona su propia cuenta, sus usuarios (manager/viewer) y sus grupos.
"""
import uuid, re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Account, User, DeviceGroup, Device, SubscriptionPlan
from .auth import require_user, require_superadmin, hash_pw
from ..scope import is_superadmin
from .. import billing

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
    return {
        "id": a.id, "name": a.name, "slug": a.slug,
        "status": a.status, "plan": a.plan,
        "contact_phone": a.contact_phone,
        "device_count": usage["device_count"],
        "usage": usage,
        "billing": billing.billing_info(a),
        "billing_cycle_end": a.billing_cycle_end.isoformat() if a.billing_cycle_end else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
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
def list_accounts(db: Session = Depends(get_db), _: User = Depends(require_superadmin)):
    return [_account_dict(a, db) for a in db.query(Account).order_by(Account.created_at.desc()).all()]


@router.post("/accounts")
def create_account(payload: AccountCreate, db: Session = Depends(get_db), _: User = Depends(require_superadmin)):
    if db.query(User).filter(User.username == payload.owner_username).first():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    acc = Account(
        id=str(uuid.uuid4()),
        name=payload.name,
        slug=_unique_slug(db, payload.name),
        status="active",
        plan=payload.plan,
        contact_phone=payload.contact_phone,
    )
    billing.init_billing_for_new_account(acc, payload.plan)  # fija vencimiento/trial
    db.add(acc)
    db.flush()  # obtener acc.id sin cerrar la transacción
    db.add(User(
        account_id=acc.id,
        username=payload.owner_username,
        password_hash=hash_pw(payload.owner_password),
        email=payload.owner_email,
        role="owner",
        full_name=payload.name,
    ))
    db.commit()
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
    # status y plan solo los cambia el superadmin
    if is_superadmin(user):
        if payload.status is not None:
            acc.status = payload.status
        if payload.plan is not None:
            acc.plan = payload.plan
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
def create_group(payload: GroupCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    acc_id = _group_account_id(payload.account_id, user)
    g = DeviceGroup(account_id=acc_id, name=payload.name)
    db.add(g)
    db.commit()
    return {"id": g.id, "name": g.name, "account_id": g.account_id}


@router.patch("/groups/{group_id}")
def rename_group(group_id: int, payload: GroupUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    g = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not g or (not is_superadmin(user) and g.account_id != user.account_id):
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    g.name = payload.name
    db.commit()
    return {"ok": True}


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    g = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not g or (not is_superadmin(user) and g.account_id != user.account_id):
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    # Desasociar routers del grupo antes de borrarlo
    db.query(Device).filter(Device.group_id == group_id).update({"group_id": None})
    db.delete(g)
    db.commit()
    return {"ok": True}
