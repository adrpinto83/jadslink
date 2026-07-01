from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional
import random, string

from ..database import get_db
from ..models import Code, Device, Command, User, Account
from .auth import require_user
from ..scope import owned_device
from .. import billing

router = APIRouter(prefix="/api/devices/{device_id}/codes", tags=["codes"])


class CodeCreate(BaseModel):
    quantity: int = 1
    duration_min: int = 60
    max_uses: int = 1
    bandwidth_dn: int = 0
    bandwidth_up: int = 0
    expires_hours: Optional[int] = None
    note: str = ""
    prefix: str = ""

    @field_validator("expires_hours", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v):
        # El formulario puede enviar "" cuando el campo se deja en blanco.
        if v == "" or v is None:
            return None
        return v


def gen_code(length=8, prefix="") -> str:
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=length))
    return f"{prefix}{code}" if prefix else code


@router.post("")
def create_codes(device_id: str, payload: CodeCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    d = owned_device(device_id, user, db)
    # Gate de estado: una cuenta suspendida/cancelada no puede emitir códigos nuevos.
    if d.account_id:
        acc = db.query(Account).filter(Account.id == d.account_id).first()
        if billing.account_blocked(acc):
            raise HTTPException(status_code=403, detail="Cuenta suspendida: no puedes generar códigos")

    # Vencimiento del código (voucher). Por defecto 30 días si no se especifica,
    # para que los códigos impresos no sean válidos indefinidamente.
    eff_hours = payload.expires_hours if payload.expires_hours else 720
    expires_at = datetime.utcnow() + timedelta(hours=eff_hours)

    codes = []
    for _ in range(min(payload.quantity, 500)):
        code = gen_code(prefix=payload.prefix)
        obj = Code(
            device_id=device_id,
            code=code,
            duration_min=payload.duration_min,
            max_uses=payload.max_uses,
            bandwidth_dn=payload.bandwidth_dn,
            bandwidth_up=payload.bandwidth_up,
            expires_at=expires_at,
            note=payload.note,
        )
        db.add(obj)
        codes.append(code)

    # Enviar códigos al dispositivo para que los active en nodogsplash
    db.add(Command(
        device_id=device_id,
        action="add_codes",
        payload={
            "codes": codes,
            "duration_min": payload.duration_min,
            "max_uses": payload.max_uses,
            "bandwidth_dn": payload.bandwidth_dn,
            "bandwidth_up": payload.bandwidth_up,
            "expires_at": int(expires_at.timestamp()),
        }
    ))
    db.commit()
    return {"created": len(codes), "codes": codes}


@router.get("")
def list_codes(device_id: str, active_only: bool = True, db: Session = Depends(get_db), user: User = Depends(require_user)):
    owned_device(device_id, user, db)
    q = db.query(Code).filter(Code.device_id == device_id)
    if active_only:
        q = q.filter(Code.active == True)
    codes = q.order_by(Code.created_at.desc()).limit(1000).all()
    return [{
        "id": c.id, "code": c.code,
        "duration_min": c.duration_min, "max_uses": c.max_uses,
        "uses": c.uses, "bandwidth_dn": c.bandwidth_dn,
        "bandwidth_up": c.bandwidth_up, "active": c.active,
        "expires_at": c.expires_at.isoformat() if c.expires_at else None,
        "created_at": c.created_at.isoformat(), "note": c.note,
    } for c in codes]


class ValidateCodeRequest(BaseModel):
    code: str
    mac: str = ""


@router.post("/validate")
def validate_code(
    device_id: str,
    payload: ValidateCodeRequest,
    x_api_key: Optional[str] = None,
    db: Session = Depends(get_db),
):
    code_str = payload.code.strip().upper()
    now = datetime.utcnow()

    # Gate de estado: si la cuenta dueña del router está suspendida, no se valida.
    device = db.query(Device).filter(Device.id == device_id).first()
    if device and device.account_id:
        acc = db.query(Account).filter(Account.id == device.account_id).first()
        if billing.account_blocked(acc):
            return {"valid": False, "reason": "account_suspended"}

    c = db.query(Code).filter(
        Code.device_id == device_id,
        Code.code == code_str,
        Code.active == True,
    ).first()

    if not c:
        return {"valid": False, "reason": "not_found"}

    if c.expires_at and c.expires_at < now:
        c.active = False
        db.commit()
        return {"valid": False, "reason": "expired"}

    if c.uses >= c.max_uses:
        return {"valid": False, "reason": "max_uses_reached"}

    c.uses += 1
    if c.uses >= c.max_uses:
        c.active = False

    db.commit()
    return {
        "valid": True,
        "duration": c.duration_min * 60,
        "bandwidth_dn": c.bandwidth_dn,
        "bandwidth_up": c.bandwidth_up,
    }


@router.delete("/{code_id}")
def revoke_code(device_id: str, code_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    owned_device(device_id, user, db)
    code = db.query(Code).filter(Code.id == code_id, Code.device_id == device_id).first()
    if not code:
        raise HTTPException(status_code=404)
    code.active = False
    db.add(Command(
        device_id=device_id,
        action="revoke_code",
        payload={"code": code.code}
    ))
    db.commit()
    return {"ok": True}


@router.get("/vouchers", response_class=HTMLResponse)
def print_vouchers(
    device_id: str,
    active_only: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    device = owned_device(device_id, user, db)

    q = db.query(Code).filter(Code.device_id == device_id)
    if active_only:
        q = q.filter(Code.active == True)
    codes = q.order_by(Code.created_at.asc()).all()

    def dur_str(minutes: int) -> str:
        h, m = divmod(minutes, 60)
        if h and m:  return f"{h}h {m}min"
        if h:        return f"{h} hora{'s' if h > 1 else ''}"
        return f"{m} min"

    vouchers_html = ""
    for c in codes:
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=110x110&data={c.code}&bgcolor=0d1b3e&color=4f8ef7&margin=4"
        vouchers_html += f"""
<div class="voucher">
  <div class="v-brand">JADSLink</div>
  <div class="v-net">{device.name}</div>
  <img class="v-qr" src="{qr_url}" alt="{c.code}">
  <div class="v-code">{c.code}</div>
  <div class="v-dur">{dur_str(c.duration_min)} de acceso WiFi</div>
  <div class="v-foot">jadsstudio.com</div>
</div>"""

    if not vouchers_html:
        vouchers_html = '<p class="empty">No hay códigos activos</p>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Vouchers — {device.name}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#e8eaf0;font-family:Arial,sans-serif;padding:20px}}
.top{{text-align:center;margin-bottom:18px}}
.top h1{{font-size:17px;color:#333;margin-bottom:10px}}
.print-btn{{padding:9px 28px;background:linear-gradient(90deg,#4f8ef7,#a259f7);color:#fff;
  border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;max-width:800px;margin:0 auto}}
.voucher{{background:#0d1b3e;border-radius:10px;padding:12px 10px;text-align:center;
  color:#fff;page-break-inside:avoid;break-inside:avoid}}
.v-brand{{font-size:13px;font-weight:800;letter-spacing:2px;
  background:linear-gradient(90deg,#4f8ef7,#a259f7);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:2px}}
.v-net{{font-size:8px;color:#7a8aaa;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.v-qr{{width:80px;height:80px;border-radius:6px;margin-bottom:6px}}
.v-code{{font-size:17px;font-weight:800;letter-spacing:4px;color:#fff;margin-bottom:3px}}
.v-dur{{font-size:8px;color:#9aa5c0;margin-bottom:8px}}
.v-foot{{font-size:7px;color:#374151;border-top:1px solid #1e3a5f;padding-top:5px}}
.empty{{grid-column:1/-1;text-align:center;color:#888;padding:40px;font-size:14px}}
@media print{{
  body{{background:#fff;padding:0}}
  .top{{margin-bottom:10px}}
  .print-btn{{display:none}}
  .grid{{max-width:100%}}
}}
</style>
</head>
<body>
<div class="top">
  <h1>Vouchers — {device.name} &nbsp;·&nbsp; {len(codes)} código{"s" if len(codes) != 1 else ""}</h1>
  <button class="print-btn" onclick="window.print()">🖨️&nbsp; Imprimir / Guardar PDF</button>
</div>
<div class="grid">{vouchers_html}</div>
</body>
</html>"""
