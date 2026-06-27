from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional
import random, string

from ..database import get_db
from ..models import Code, Device, Command

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
def create_codes(device_id: str, payload: CodeCreate, db: Session = Depends(get_db)):
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404)

    expires_at = None
    if payload.expires_hours:
        expires_at = datetime.utcnow() + timedelta(hours=payload.expires_hours)

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
        }
    ))
    db.commit()
    return {"created": len(codes), "codes": codes}


@router.get("")
def list_codes(device_id: str, active_only: bool = True, db: Session = Depends(get_db)):
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
def revoke_code(device_id: str, code_id: int, db: Session = Depends(get_db)):
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
