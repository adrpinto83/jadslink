"""Service for handling upgrade requests and payments."""

from models.tenant import Tenant, PlanTier
from models.upgrade_request import UpgradeRequest, PaymentStatus, UpgradeType, PaymentMethod
from models.pricing_config import PricingConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import logging

log = logging.getLogger("jadslink.upgrade_service")


class UpgradeService:
    """Service for managing tenant upgrades and payment requests."""

    @staticmethod
    async def get_exchange_rate(db: AsyncSession | None = None) -> Decimal:
        """
        Get current official exchange rate USD -> VEF from database.
        Dynamically updated via scraping + fallback API.
        """
        if db is None:
            # Fallback if no DB session provided
            return Decimal("36.50")

        from services.exchange_rate_service import ExchangeRateService

        return await ExchangeRateService.get_current_rate(db)

    @staticmethod
    async def create_upgrade_request(
        tenant: Tenant,
        upgrade_type: str,
        payment_method: str,
        ticket_quantity: int | None = None,
        new_plan_tier: str | None = None,
        payment_details: dict | None = None,
        db: AsyncSession | None = None,
    ) -> tuple[UpgradeRequest, str]:
        """
        Crea una nueva solicitud de upgrade/pago.

        Retorna: (upgrade_request, message)
        """

        # Validar tipo de upgrade
        if upgrade_type == "extra_tickets":
            if not ticket_quantity or ticket_quantity <= 0:
                return None, "La cantidad de tickets debe ser mayor a 0"
            # Cada 50 tickets cuesta $0.50
            amount_usd = Decimal("0.50")
        elif upgrade_type == "plan_upgrade":
            if not new_plan_tier or new_plan_tier not in ["basic", "pro"]:
                return None, "Plan inválido"
            # Precios de planes
            plan_prices = {
                "basic": Decimal("29.00"),   # $29/mes
                "pro": Decimal("99.00"),     # $99/mes
            }
            amount_usd = plan_prices.get(new_plan_tier)
        else:
            return None, "Tipo de upgrade inválido"

        # Obtener tasa de cambio
        exchange_rate = await UpgradeService.get_exchange_rate(db)
        amount_vef = amount_usd * exchange_rate

        # Crear solicitud
        upgrade_request = UpgradeRequest(
            tenant_id=tenant.id,
            upgrade_type=upgrade_type,
            ticket_quantity=ticket_quantity if upgrade_type == "extra_tickets" else None,
            new_plan_tier=new_plan_tier if upgrade_type == "plan_upgrade" else None,
            payment_method=payment_method,
            amount_usd=amount_usd,
            amount_vef=amount_vef,
            exchange_rate=exchange_rate,
            status=PaymentStatus.pending_payment,
        )

        # Guardar detalles de pago según método
        if payment_method == "mobile_pay":
            upgrade_request.banco_origen = payment_details.get("banco_origen")
            upgrade_request.cédula_pagador = payment_details.get("cédula_pagador")
            upgrade_request.referencia_pago = payment_details.get("referencia_pago")
            upgrade_request.comprobante_url = payment_details.get("comprobante_url")
            upgrade_request.payment_details = payment_details

        elif payment_method == "card":
            # Aquí se integraría Stripe en el futuro
            upgrade_request.payment_details = {"token": payment_details.get("token")}

        if db:
            db.add(upgrade_request)
            await db.flush()

        message = f"Solicitud de {upgrade_type} creada. Monto: ${amount_usd} USD (Bs. {amount_vef} aprox. a tasa oficial)"
        return upgrade_request, message

    @staticmethod
    async def approve_payment(
        upgrade_request: UpgradeRequest,
        admin_email: str,
        admin_notes: str = "",
        db: AsyncSession | None = None,
    ) -> tuple[bool, str]:
        """
        Admin aprueba un pago y aplica los cambios al tenant.

        Retorna: (success: bool, message: str)
        """

        try:
            # Obtener tenant
            tenant = upgrade_request.tenant

            # Aplicar cambios según tipo de upgrade
            if upgrade_request.upgrade_type == "extra_tickets":
                # Agregar paquetes de 50 tickets
                packs = (upgrade_request.ticket_quantity + 49) // 50
                tenant.extra_tickets_count = (tenant.extra_tickets_count or 0) + packs
                message = f"Se agregaron {packs * 50} tickets adicionales al tenant"

            elif upgrade_request.upgrade_type == "plan_upgrade":
                # Cambiar plan
                old_plan = tenant.plan_tier
                tenant.plan_tier = upgrade_request.new_plan_tier
                tenant.subscription_status = "active"
                message = f"Plan actualizado de {old_plan} a {upgrade_request.new_plan_tier}"

            # Actualizar estado de solicitud
            upgrade_request.status = PaymentStatus.approved
            upgrade_request.approved_by = admin_email
            upgrade_request.admin_notes = admin_notes

            if db:
                db.add(upgrade_request)
                db.add(tenant)
                await db.flush()

            log.info(f"Payment approved: {upgrade_request.id} by {admin_email}")

            # Enviar email de aprobación
            from services.email_service import EmailService

            tenant_email = tenant.users[0].email if tenant.users else None
            if tenant_email:
                await EmailService.send_payment_approved(
                    tenant_email=tenant_email,
                    tenant_name=tenant.name,
                    amount_usd=float(upgrade_request.amount_usd),
                    amount_vef=float(upgrade_request.amount_vef or 0),
                    upgrade_type=upgrade_request.upgrade_type,
                )

            return True, message

        except Exception as e:
            log.error(f"Error approving payment: {str(e)}")
            return False, f"Error al aprobar: {str(e)}"

    @staticmethod
    async def reject_payment(
        upgrade_request: UpgradeRequest,
        admin_email: str,
        rejection_reason: str,
        db: AsyncSession | None = None,
    ) -> tuple[bool, str]:
        """
        Admin rechaza un pago.

        Retorna: (success: bool, message: str)
        """

        try:
            upgrade_request.status = PaymentStatus.rejected
            upgrade_request.approved_by = admin_email
            upgrade_request.rejection_reason = rejection_reason

            if db:
                db.add(upgrade_request)
                await db.flush()

            log.info(f"Payment rejected: {upgrade_request.id} by {admin_email}")

            # Enviar email de rechazo
            from services.email_service import EmailService

            tenant_email = upgrade_request.tenant.users[0].email if upgrade_request.tenant.users else None
            if tenant_email:
                await EmailService.send_payment_rejected(
                    tenant_email=tenant_email,
                    tenant_name=upgrade_request.tenant.name,
                    amount_usd=float(upgrade_request.amount_usd),
                    rejection_reason=rejection_reason,
                )

            return True, "Pago rechazado correctamente"

        except Exception as e:
            log.error(f"Error rejecting payment: {str(e)}")
            return False, f"Error al rechazar: {str(e)}"

    @staticmethod
    async def send_payment_reminder(
        upgrade_request: UpgradeRequest,
        db: AsyncSession | None = None,
    ) -> bool:
        """
        Envía recordatorio de pago pendiente.
        """

        try:
            # Incrementar contador de recordatorios
            upgrade_request.reminder_count = (upgrade_request.reminder_count or 0) + 1
            upgrade_request.last_reminder_at = datetime.now(timezone.utc).isoformat()

            # Enviar email al tenant
            from services.email_service import EmailService

            tenant_email = upgrade_request.tenant.users[0].email if upgrade_request.tenant.users else None
            if tenant_email:
                days_pending = (datetime.now(timezone.utc) - upgrade_request.created_at).days
                await EmailService.send_payment_reminder(
                    tenant_email=tenant_email,
                    tenant_name=upgrade_request.tenant.name,
                    amount_usd=float(upgrade_request.amount_usd),
                    amount_vef=float(upgrade_request.amount_vef or 0),
                    days_pending=days_pending,
                )

            log.info(f"Reminder sent for: {upgrade_request.id} (count: {upgrade_request.reminder_count})")

            if db:
                db.add(upgrade_request)
                await db.flush()

            return True

        except Exception as e:
            log.error(f"Error sending reminder: {str(e)}")
            return False

    @staticmethod
    async def get_pending_payments(
        db: AsyncSession,
        days_pending: int | None = None,
    ) -> list[UpgradeRequest]:
        """
        Obtiene todas las solicitudes de pago pendientes.
        Opcionalmente filtra por días pendientes.
        """

        query = select(UpgradeRequest).where(
            UpgradeRequest.status == PaymentStatus.pending_payment
        )

        if days_pending:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_pending)
            query = query.where(UpgradeRequest.created_at >= cutoff_date)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def process_payment_reminders(db: AsyncSession) -> dict:
        """
        Job periódico que envía recordatorios de pago.
        Se ejecuta cada día vía APScheduler.

        Envía recordatorios progresivos:
        - 3 días: Primer recordatorio
        - 7 días: Segundo recordatorio
        - 14 días: Último recordatorio + advertencia de bloqueo
        """

        now = datetime.now(timezone.utc)

        pending = await UpgradeService.get_pending_payments(db)

        stats = {
            "total_processed": 0,
            "reminders_sent": 0,
            "blocked": 0,
            "errors": 0,
        }

        for request in pending:
            days_pending = (now - request.created_at).days

            # Enviar recordatorios en días específicos
            should_remind = False

            if days_pending == 3 and request.reminder_count == 0:
                should_remind = True
            elif days_pending == 7 and request.reminder_count < 2:
                should_remind = True
            elif days_pending == 14 and request.reminder_count < 3:
                should_remind = True

            if should_remind:
                success = await UpgradeService.send_payment_reminder(request, db)
                if success:
                    stats["reminders_sent"] += 1
                else:
                    stats["errors"] += 1

            stats["total_processed"] += 1

        await db.commit()

        log.info(f"Payment reminder job completed: {stats}")
        return stats
