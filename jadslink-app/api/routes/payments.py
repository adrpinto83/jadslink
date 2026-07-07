"""Pagos de suscripción: reporte con comprobante, aprobación y servido del comprobante.

Flujo semi-manual (pagos locales Venezuela):
  operador reporta pago + comprobante  →  superadmin aprueba  →  se extiende el ciclo.
"""
import os, uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..database import get_db, DATA_DIR
from ..models import Payment, Account, User
from .auth import require_user, require_superadmin
from ..scope import is_superadmin
from .. import billing, emailer

router = APIRouter(prefix="/api", tags=["payments"])

METHODS = {"pago_movil", "transferencia", "zelle", "usdt", "efectivo"}
PROOFS_DIR = os.path.join(DATA_DIR, "proofs")
os.makedirs(PROOFS_DIR, exist_ok=True)
MAX_PROOF_BYTES = 4 * 1024 * 1024  # 4 MB


class RejectPayload(BaseModel):
    note: str = ""


def _can_manage_account(user: User, account_id: str) -> bool:
    return is_superadmin(user) or (user.account_id == account_id and user.role == "owner")


def _payment_dict(p: Payment, account_name: str = "") -> dict:
    return {
        "id": p.id, "account_id": p.account_id, "account_name": account_name,
        "amount_usd": p.amount_usd, "method": p.method, "reference": p.reference,
        "note": p.note, "status": p.status, "has_proof": bool(p.proof_file),
        "period_start": p.period_start.isoformat() if p.period_start else None,
        "period_end": p.period_end.isoformat() if p.period_end else None,
        "review_note": p.review_note,
        "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


# ── Reportar pago ────────────────────────────────────────────────────────────────

@router.post("/accounts/{account_id}/payments")
async def report_payment(
    account_id: str,
    amount_usd: float = Form(...),
    method: str = Form(...),
    reference: str = Form(""),
    note: str = Form(""),
    proof: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    if not _can_manage_account(user, account_id):
        raise HTTPException(status_code=403, detail="Sin permiso")
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if method not in METHODS:
        raise HTTPException(status_code=400, detail="Método de pago inválido")
    if amount_usd <= 0:
        raise HTTPException(status_code=400, detail="Monto inválido")

    proof_name = ""
    if proof is not None and proof.filename:
        data = await proof.read()
        if len(data) > MAX_PROOF_BYTES:
            raise HTTPException(status_code=400, detail="El comprobante supera 4 MB")
        ext = os.path.splitext(proof.filename)[1][:8].lower()
        proof_name = f"{uuid.uuid4().hex}{ext}"
        with open(os.path.join(PROOFS_DIR, proof_name), "wb") as f:
            f.write(data)

    p = Payment(
        account_id=account_id, amount_usd=amount_usd, method=method,
        reference=reference, note=note, proof_file=proof_name, status="pending",
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    emailer.notify(
        db,
        f"[JADSLink] Nuevo pago de suscripción — {acc.name}",
        f"Cuenta: {acc.name}\nMonto: ${amount_usd:.2f}\nMétodo: {method}\n"
        f"Referencia: {reference or '—'}\nNota: {note or '—'}\n"
        f"Comprobante: {'sí' if proof_name else 'no'}\n\n"
        f"Apruébalo desde el panel de superadmin:\nhttps://link.jadsstudio.com",
    )
    return _payment_dict(p, acc.name)


# ── Listar pagos de una cuenta ──────────────────────────────────────────────────

@router.get("/accounts/{account_id}/payments")
def list_account_payments(account_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    if not is_superadmin(user) and user.account_id != account_id:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    acc = db.query(Account).filter(Account.id == account_id).first()
    name = acc.name if acc else ""
    pays = db.query(Payment).filter(Payment.account_id == account_id)\
             .order_by(Payment.created_at.desc()).all()
    return [_payment_dict(p, name) for p in pays]


# ── Cola de aprobación (superadmin) ──────────────────────────────────────────────

@router.get("/payments")
def list_payments(status: Optional[str] = None, db: Session = Depends(get_db), _: User = Depends(require_superadmin)):
    q = db.query(Payment, Account.name).join(Account, Payment.account_id == Account.id)
    if status:
        q = q.filter(Payment.status == status)
    rows = q.order_by(Payment.created_at.desc()).limit(500).all()
    return [_payment_dict(p, name) for p, name in rows]


@router.post("/payments/{payment_id}/approve")
def approve_payment(payment_id: int, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    if p.status != "pending":
        raise HTTPException(status_code=400, detail="El pago ya fue procesado")
    acc = db.query(Account).filter(Account.id == p.account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    start, end = billing.approve_and_extend(acc)
    p.status = "approved"
    p.period_start, p.period_end = start, end
    p.reviewed_by, p.reviewed_at = user.id, datetime.utcnow()
    db.commit()
    return {"ok": True, "billing_cycle_end": end.isoformat(), "account_status": acc.status}


@router.post("/payments/{payment_id}/reject")
def reject_payment(payment_id: int, payload: RejectPayload, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    if p.status != "pending":
        raise HTTPException(status_code=400, detail="El pago ya fue procesado")
    p.status = "rejected"
    p.review_note = payload.note
    p.reviewed_by, p.reviewed_at = user.id, datetime.utcnow()
    db.commit()
    return {"ok": True}


# ── Comprobante ──────────────────────────────────────────────────────────────────

@router.get("/payments/{payment_id}/proof")
def get_proof(payment_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p or not p.proof_file:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    if not is_superadmin(user) and user.account_id != p.account_id:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    path = os.path.join(PROOFS_DIR, p.proof_file)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Archivo no disponible")
    return FileResponse(path)
