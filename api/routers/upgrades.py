"""Routes for upgrade requests and payment management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from uuid import UUID

from database import get_db
from deps import get_current_user, get_current_tenant
from models.user import User
from models.tenant import Tenant
from models.upgrade_request import UpgradeRequest, PaymentStatus
from schemas.upgrade_request import (
    UpgradeRequestCreate,
    UpgradeRequestResponse,
    AdminPaymentConfirm,
    PendingPaymentResponse,
)
from services.upgrade_service import UpgradeService
import logging

log = logging.getLogger("jadslink.upgrades")

router = APIRouter()


# ============================================================================
# CLIENTE - Solicitar upgrade/pago
# ============================================================================


@router.post("/request-upgrade", response_model=UpgradeRequestResponse, status_code=status.HTTP_201_CREATED)
async def request_upgrade(
    request: UpgradeRequestCreate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Cliente solicita un upgrade (tickets adicionales o cambio de plan).

    Ejemplo:
    POST /api/v1/subscriptions/request-upgrade
    {
        "upgrade_type": "extra_tickets",
        "ticket_quantity": 50,
        "payment_method": "pago_movil",
        "payment_details": {
            "banco_origen": "BDO",
            "cédula_pagador": "12345678",
            "referencia_pago": "1234567890",
            "comprobante_url": "https://..."
        }
    }
    """

    if not current_tenant:
        raise HTTPException(status_code=403, detail="No tenant found")

    # Validar datos de pago si es Pago Móvil
    if request.payment_method == "pago_movil" and request.payment_details:
        from utils.validators import validate_cedula, validate_referencia, validate_banco

        # Validate banco
        banco = request.payment_details.get("banco_origen", "")
        is_valid, error_or_value = validate_banco(banco)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Banco inválido: {error_or_value}")

        # Validate cédula
        cedula = request.payment_details.get("cédula_pagador", "")
        is_valid, error_or_value = validate_cedula(cedula)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Cédula inválida: {error_or_value}")
        # Update with normalized cédula
        request.payment_details["cédula_pagador"] = error_or_value

        # Validate referencia
        referencia = request.payment_details.get("referencia_pago", "")
        is_valid, error_or_value = validate_referencia(referencia)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Referencia inválida: {error_or_value}")
        # Update with normalized referencia
        request.payment_details["referencia_pago"] = error_or_value

    # Crear solicitud
    upgrade_request, message = await UpgradeService.create_upgrade_request(
        tenant=current_tenant,
        upgrade_type=request.upgrade_type,
        payment_method=request.payment_method,
        ticket_quantity=request.ticket_quantity,
        new_plan_tier=request.new_plan_tier,
        payment_details=request.payment_details or {},
        db=db,
    )

    if not upgrade_request:
        raise HTTPException(status_code=400, detail=message)

    await db.commit()
    await db.refresh(upgrade_request)

    log.info(f"Upgrade request created: {upgrade_request.id} for tenant {current_tenant.id}")

    # Enviar email de confirmación de recepción
    from services.email_service import EmailService

    tenant_email = current_tenant.users[0].email if current_tenant.users else None
    if tenant_email:
        await EmailService.send_payment_received(
            tenant_email=tenant_email,
            tenant_name=current_tenant.name,
            amount_usd=float(upgrade_request.amount_usd),
        )

    return upgrade_request


@router.get("/my-requests", response_model=list[UpgradeRequestResponse])
async def get_my_upgrade_requests(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Cliente ve todas sus solicitudes de upgrade/pago.
    """

    if not current_tenant:
        raise HTTPException(status_code=403, detail="No tenant found")

    result = await db.execute(
        select(UpgradeRequest)
        .where(UpgradeRequest.tenant_id == current_tenant.id)
        .order_by(UpgradeRequest.created_at.desc())
    )

    return result.scalars().all()


# ============================================================================
# ADMIN - Confirmar/Rechazar pagos
# ============================================================================


@router.get("/admin/pending-payments", response_model=list[PendingPaymentResponse])
async def get_pending_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin ve todas las solicitudes de pago pendientes.
    """

    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Solo superadmin puede ver pagos pendientes")

    pending = await UpgradeService.get_pending_payments(db)

    responses = []
    for req in pending:
        days_pending = (datetime.now(timezone.utc) - req.created_at).days
        primary_user = req.tenant.users[0] if req.tenant.users else None

        response = PendingPaymentResponse(
            id=req.id,
            tenant_name=req.tenant.name,
            contact_email=primary_user.email if primary_user else "noemail@jadslink.io",
            upgrade_type=req.upgrade_type,
            amount_usd=req.amount_usd,
            amount_vef=req.amount_vef,
            exchange_rate=req.exchange_rate,
            payment_method=req.payment_method,
            status=req.status,
            banco_origen=req.banco_origen,
            referencia_pago=req.referencia_pago,
            comprobante_url=req.comprobante_url,
            created_at=req.created_at,
            days_pending=days_pending,
            reminder_count=req.reminder_count or 0,
        )
        responses.append(response)

    return responses


@router.post("/admin/confirm-payment/{upgrade_id}")
async def confirm_payment(
    upgrade_id: UUID,
    confirm: AdminPaymentConfirm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin aprueba o rechaza un pago.

    Ejemplo:
    POST /api/v1/subscriptions/admin/confirm-payment/{upgrade_id}
    {
        "action": "approve",
        "notes": "Pago verificado en cuenta bancaria"
    }
    """

    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Solo superadmin puede confirmar pagos")

    # Obtener solicitud
    result = await db.execute(
        select(UpgradeRequest).where(UpgradeRequest.id == upgrade_id)
    )
    upgrade_request = result.scalar_one_or_none()

    if not upgrade_request:
        raise HTTPException(status_code=404, detail="Upgrade request not found")

    if upgrade_request.status != PaymentStatus.pending_payment:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden confirmar pagos con estado 'pending_payment'. Estado actual: {upgrade_request.status}",
        )

    if confirm.action == "approve":
        success, message = await UpgradeService.approve_payment(
            upgrade_request=upgrade_request,
            admin_email=current_user.email,
            admin_notes=confirm.notes,
            db=db,
        )
    elif confirm.action == "reject":
        if not confirm.notes:
            raise HTTPException(status_code=400, detail="Debes proporcionar un motivo de rechazo")

        success, message = await UpgradeService.reject_payment(
            upgrade_request=upgrade_request,
            admin_email=current_user.email,
            rejection_reason=confirm.notes,
            db=db,
        )
    else:
        raise HTTPException(status_code=400, detail="Acción inválida")

    await db.commit()

    if not success:
        raise HTTPException(status_code=500, detail=message)

    log.info(f"Payment {confirm.action}: {upgrade_id} by {current_user.email}")

    return {
        "status": "success",
        "action": confirm.action,
        "message": message,
        "upgrade_id": str(upgrade_id),
    }


@router.get("/admin/payment-history")
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = None,
    limit: int = 100,
):
    """
    Admin ve historial de todos los pagos.
    Puede filtrar por estado: pending_payment, approved, rejected
    """

    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Solo superadmin puede ver historial de pagos")

    query = select(UpgradeRequest).order_by(UpgradeRequest.created_at.desc()).limit(limit)

    if status_filter and status_filter in [s.value for s in PaymentStatus]:
        query = query.where(UpgradeRequest.status == status_filter)

    result = await db.execute(query)
    upgrade_requests = result.scalars().all()

    responses = []
    for req in upgrade_requests:
        days_pending = (datetime.now(timezone.utc) - req.created_at).days
        primary_user = req.tenant.users[0] if req.tenant.users else None

        response = {
            "id": str(req.id),
            "tenant_name": req.tenant.name,
            "contact_email": primary_user.email if primary_user else "noemail@jadslink.io",
            "upgrade_type": req.upgrade_type,
            "amount_usd": float(req.amount_usd),
            "amount_vef": float(req.amount_vef) if req.amount_vef else None,
            "exchange_rate": float(req.exchange_rate) if req.exchange_rate else None,
            "payment_method": req.payment_method,
            "status": req.status,
            "banco_origen": req.banco_origen,
            "referencia_pago": req.referencia_pago,
            "comprobante_url": req.comprobante_url,
            "created_at": req.created_at.isoformat(),
            "days_pending": days_pending,
            "reminder_count": req.reminder_count or 0,
            "approved_by": req.approved_by,
            "admin_notes": req.admin_notes,
        }
        responses.append(response)

    return responses
