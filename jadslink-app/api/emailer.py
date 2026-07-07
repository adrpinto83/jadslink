"""Envío de alertas por email (SMTP configurado vía variables de entorno).

Un solo destinatario global (Settings.alert_email), gateado por
Settings.alert_enabled — mismo esquema que la alerta de nodo offline.
"""
import os
import smtplib
import logging
from email.message import EmailMessage
from sqlalchemy.orm import Session

from .models import Settings

log = logging.getLogger("jadslink")


def alerts_enabled(db: Session) -> bool:
    row = db.query(Settings).filter(Settings.key == "alert_enabled").first()
    return bool(row and row.value == "true")


def get_alert_recipient(db: Session) -> str:
    row = db.query(Settings).filter(Settings.key == "alert_email").first()
    return row.value if row else ""


def send_email(subject: str, body: str, to: str) -> None:
    host = os.getenv("SMTP_HOST", "")
    if not host or not to:
        return
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    pw = os.getenv("SMTP_PASS", "")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user or "noreply@jadsstudio.com"
    msg["To"] = to
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            if user and pw:
                s.login(user, pw)
            s.send_message(msg)
    except Exception:
        log.exception("No se pudo enviar el email: %s", subject)


def notify(db: Session, subject: str, body: str) -> None:
    """Envía al destinatario global de alertas si están habilitadas."""
    if not alerts_enabled(db):
        return
    to = get_alert_recipient(db)
    if to:
        send_email(subject, body, to)
