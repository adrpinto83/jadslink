"""Service for sending transactional emails via Resend."""

import asyncio
from config import get_settings
import logging

log = logging.getLogger("jadslink.email")

settings = get_settings()

# Import Resend only if API key is configured
RESEND_AVAILABLE = bool(settings.RESEND_API_KEY)

if RESEND_AVAILABLE:
    import resend

    resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """Service for sending transactional emails"""

    @staticmethod
    def _send_email_sync(
        to_email: str,
        subject: str,
        html_body: str,
    ) -> bool:
        """
        Send email synchronously via Resend.
        (Note: Resend doesn't have async support yet, so we run in executor)

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML content

        Returns:
            True if sent successfully
        """
        if not RESEND_AVAILABLE:
            log.warning(f"Email not sent (Resend not configured): {to_email} - {subject}")
            return False

        try:
            response = resend.Emails.send(
                {
                    "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                    "to": to_email,
                    "subject": subject,
                    "html": html_body,
                }
            )

            log.info(f"Email sent to {to_email}: {subject} (ID: {response.get('id')})")
            return True

        except Exception as e:
            log.error(f"Failed to send email to {to_email}: {e}")
            return False

    @staticmethod
    async def send_email_async(
        to_email: str,
        subject: str,
        html_body: str,
    ) -> bool:
        """
        Send email asynchronously (runs sync code in executor).

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML content

        Returns:
            True if sent successfully
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            EmailService._send_email_sync,
            to_email,
            subject,
            html_body,
        )

    @staticmethod
    async def send_payment_approved(
        tenant_email: str,
        tenant_name: str,
        amount_usd: float,
        amount_vef: float,
        upgrade_type: str,
    ) -> bool:
        """
        Send payment approval notification.
        """
        upgrade_label = (
            "Tickets Adicionales" if upgrade_type == "extra_tickets" else "Upgrade de Plan"
        )

        html = f"""
        <html>
          <head><meta charset="UTF-8"></head>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px;">
              <h2 style="color: #2563eb; text-align: center;">✅ Pago Aprobado</h2>
              <p>Hola <strong>{tenant_name}</strong>,</p>
              <p>¡Excelentes noticias! Tu pago ha sido confirmado exitosamente.</p>

              <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Tipo:</strong> {upgrade_label}</p>
                <p><strong>Monto:</strong> ${amount_usd:.2f} USD (Bs. {amount_vef:.2f})</p>
                <p style="margin: 0;"><strong>Estatus:</strong> <span style="color: #16a34a; font-weight: bold;">Confirmado</span></p>
              </div>

              <p>Los beneficios de tu compra han sido aplicados a tu cuenta. Ahora puedes acceder a todas las funcionalidades incluidas en tu plan.</p>

              <p style="text-align: center; margin: 30px 0;">
                <a href="https://link.jadsstudio.com.ve/dashboard" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                  Ir al Dashboard
                </a>
              </p>

              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #666; font-size: 12px; text-align: center;">
                Si tienes preguntas, no dudes en contactarnos: <a href="mailto:{settings.SUPPORT_EMAIL}" style="color: #2563eb;">{settings.SUPPORT_EMAIL}</a>
              </p>
              <p style="color: #666; font-size: 12px; text-align: center; margin-top: 10px;">
                JADSlink © 2026 | Plataforma SaaS de Conectividad Satelital
              </p>
            </div>
          </body>
        </html>
        """

        return await EmailService.send_email_async(
            to_email=tenant_email,
            subject="✅ Pago Aprobado - JADSlink",
            html_body=html,
        )

    @staticmethod
    async def send_payment_rejected(
        tenant_email: str,
        tenant_name: str,
        amount_usd: float,
        rejection_reason: str,
    ) -> bool:
        """
        Send payment rejection notification.
        """
        html = f"""
        <html>
          <head><meta charset="UTF-8"></head>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px;">
              <h2 style="color: #dc2626; text-align: center;">❌ Pago Rechazado</h2>
              <p>Hola <strong>{tenant_name}</strong>,</p>
              <p>Lamentablemente no pudimos confirmar tu pago.</p>

              <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
                <p><strong>Motivo del rechazo:</strong></p>
                <p style="margin: 10px 0;">{rejection_reason}</p>
              </div>

              <p><strong>Monto:</strong> ${amount_usd:.2f} USD</p>

              <p>Por favor verifica los datos de tu transferencia y vuelve a intentarlo. Si el problema persiste, contáctanos para más ayuda.</p>

              <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                <p style="margin: 0;"><strong>💬 Soporte:</strong> <a href="mailto:{settings.SUPPORT_EMAIL}" style="color: #2563eb;">{settings.SUPPORT_EMAIL}</a></p>
              </div>

              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #666; font-size: 12px; text-align: center;">
                JADSlink © 2026 | Plataforma SaaS de Conectividad Satelital
              </p>
            </div>
          </body>
        </html>
        """

        return await EmailService.send_email_async(
            to_email=tenant_email,
            subject="❌ Pago Rechazado - JADSlink",
            html_body=html,
        )

    @staticmethod
    async def send_payment_reminder(
        tenant_email: str,
        tenant_name: str,
        amount_usd: float,
        amount_vef: float,
        days_pending: int,
    ) -> bool:
        """
        Send payment reminder notification.
        """
        html = f"""
        <html>
          <head><meta charset="UTF-8"></head>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px;">
              <h2 style="color: #f59e0b; text-align: center;">⏳ Recordatorio: Pago Pendiente</h2>
              <p>Hola <strong>{tenant_name}</strong>,</p>
              <p>Tienes una solicitud de pago en espera de confirmación.</p>

              <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Monto:</strong> ${amount_usd:.2f} USD (Bs. {amount_vef:.2f})</p>
                <p><strong>Días en espera:</strong> {days_pending} días</p>
                <p style="margin: 0; color: #b45309;"><strong>⚠️ Por favor completa tu pago pronto</strong></p>
              </div>

              <p>Si ya realizaste la transferencia, nuestro equipo la estará procesando. Si tienes preguntas sobre el estado de tu pago, contáctanos.</p>

              <p style="text-align: center; margin: 30px 0;">
                <a href="https://link.jadsstudio.com.ve/dashboard/billing" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                  Ver Estado del Pago
                </a>
              </p>

              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #666; font-size: 12px; text-align: center;">
                Preguntas: <a href="mailto:{settings.SUPPORT_EMAIL}" style="color: #2563eb;">{settings.SUPPORT_EMAIL}</a>
              </p>
              <p style="color: #666; font-size: 12px; text-align: center; margin-top: 10px;">
                JADSlink © 2026
              </p>
            </div>
          </body>
        </html>
        """

        return await EmailService.send_email_async(
            to_email=tenant_email,
            subject=f"⏳ Recordatorio: Pago Pendiente ({days_pending} días) - JADSlink",
            html_body=html,
        )

    @staticmethod
    async def send_payment_received(
        tenant_email: str,
        tenant_name: str,
        amount_usd: float,
    ) -> bool:
        """
        Send payment received notification.
        """
        html = f"""
        <html>
          <head><meta charset="UTF-8"></head>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px;">
              <h2 style="color: #2563eb; text-align: center;">📬 Solicitud de Pago Recibida</h2>
              <p>Hola <strong>{tenant_name}</strong>,</p>
              <p>¡Excelente! Hemos recibido tu solicitud de pago.</p>

              <div style="background: #dbeafe; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Monto:</strong> ${amount_usd:.2f} USD</p>
                <p style="margin: 0;"><strong>Estatus:</strong> <span style="color: #2563eb; font-weight: bold;">En revisión</span></p>
              </div>

              <p>Nuestro equipo revisará tu comprobante en las próximas <strong>24-48 horas</strong>. Te enviaremos un email cuando el pago sea confirmado.</p>

              <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #166534;"><strong>✓ Si ya realizaste el pago, esto es todo por ahora</strong></p>
              </div>

              <p style="text-align: center; margin: 30px 0;">
                <a href="https://link.jadsstudio.com.ve/dashboard/billing" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                  Ver solicitudes de pago
                </a>
              </p>

              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              <p style="color: #666; font-size: 12px; text-align: center;">
                ¡Gracias por tu paciencia!
              </p>
              <p style="color: #666; font-size: 12px; text-align: center; margin-top: 10px;">
                JADSlink © 2026
              </p>
            </div>
          </body>
        </html>
        """

        return await EmailService.send_email_async(
            to_email=tenant_email,
            subject="📬 Solicitud de Pago Recibida - JADSlink",
            html_body=html,
        )
