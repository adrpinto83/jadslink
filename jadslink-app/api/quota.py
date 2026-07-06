"""Lógica de cuotas de tickets por plan.

Sistema de cuotas:
- Cada plan tiene un límite mensual de tickets (tickets_per_month, 0 = ilimitado)
- Las cuentas acumulan tickets usados (tickets_used_this_month)
- El superadmin puede otorgar tickets bonus (bonus_tickets)
- Los tickets bonus NO se resetean mensualmente
- El reset mensual ocurre cuando ticket_quota_reset_at < ahora
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .models import Account, SubscriptionPlan, TicketQuotaLog


def get_plan(db: Session, plan_key: str) -> SubscriptionPlan | None:
    """Obtiene un plan por su clave."""
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.key == plan_key).first()


def _ensure_quota_reset(db: Session, account: Account) -> None:
    """Si pasó el periodo mensual, resetea el contador."""
    now = datetime.utcnow()
    if account.ticket_quota_reset_at is None or account.ticket_quota_reset_at <= now:
        # Registrar el reset si hubo uso
        if account.tickets_used_this_month > 0:
            db.add(TicketQuotaLog(
                account_id=account.id,
                action="reset_monthly",
                quantity=account.tickets_used_this_month,
                note=f"Reset mensual automático",
            ))
        account.tickets_used_this_month = 0
        account.ticket_quota_reset_at = now + timedelta(days=30)


def get_quota_info(db: Session, account: Account) -> dict:
    """Devuelve información de la cuota de tickets de una cuenta."""
    if account is None:
        return {"limit": 0, "used": 0, "bonus": 0, "available": 0, "unlimited": True}

    _ensure_quota_reset(db, account)
    plan = get_plan(db, account.plan)
    limit = plan.tickets_per_month if plan else 0
    unlimited = limit == 0

    used = account.tickets_used_this_month or 0
    bonus = account.bonus_tickets or 0

    if unlimited:
        available = -1  # -1 indica ilimitado
    else:
        # Disponibles = (límite - usados) + bonus
        base_remaining = max(0, limit - used)
        available = base_remaining + bonus

    return {
        "plan": account.plan,
        "limit": limit,
        "used": used,
        "bonus": bonus,
        "available": available,
        "unlimited": unlimited,
        "reset_at": account.ticket_quota_reset_at.isoformat() if account.ticket_quota_reset_at else None,
    }


def can_generate_tickets(db: Session, account: Account, quantity: int) -> tuple[bool, str]:
    """
    Verifica si la cuenta puede generar N tickets.

    Returns:
        (True, "") si puede generar
        (False, "mensaje de error") si no puede
    """
    if account is None:
        return False, "Cuenta no encontrada"

    if account.deleted_at is not None:
        return False, "Cuenta eliminada"

    _ensure_quota_reset(db, account)
    plan = get_plan(db, account.plan)

    if plan is None:
        return False, "Plan no válido"

    # Plan con tickets ilimitados
    if plan.tickets_per_month == 0:
        return True, ""

    limit = plan.tickets_per_month
    used = account.tickets_used_this_month or 0
    bonus = account.bonus_tickets or 0

    # Calcular disponibles: (límite - usados) + bonus
    base_remaining = max(0, limit - used)
    available = base_remaining + bonus

    if quantity > available:
        return False, f"Cuota agotada. Disponibles: {available}, solicitados: {quantity}"

    return True, ""


def consume_tickets(db: Session, account: Account, quantity: int) -> None:
    """
    Consume tickets de la cuota de una cuenta.
    Primero usa del límite mensual, luego de los bonus.
    """
    if account is None or quantity <= 0:
        return

    _ensure_quota_reset(db, account)
    plan = get_plan(db, account.plan)

    # Si el plan es ilimitado, solo registramos el uso
    if plan and plan.tickets_per_month == 0:
        db.add(TicketQuotaLog(
            account_id=account.id,
            action="usage",
            quantity=quantity,
            note="Plan ilimitado",
        ))
        db.flush()
        return

    limit = plan.tickets_per_month if plan else 0
    used = account.tickets_used_this_month or 0
    bonus = account.bonus_tickets or 0

    # Calcular cuántos vienen del límite mensual vs bonus
    base_remaining = max(0, limit - used)

    if quantity <= base_remaining:
        # Todo viene del límite mensual
        account.tickets_used_this_month = used + quantity
        from_base = quantity
        from_bonus = 0
    else:
        # Primero agotamos el límite mensual, luego bonus
        from_base = base_remaining
        from_bonus = quantity - base_remaining
        account.tickets_used_this_month = limit
        account.bonus_tickets = max(0, bonus - from_bonus)

    # Registrar el uso
    note_parts = []
    if from_base > 0:
        note_parts.append(f"{from_base} de cuota mensual")
    if from_bonus > 0:
        note_parts.append(f"{from_bonus} de bonus")

    db.add(TicketQuotaLog(
        account_id=account.id,
        action="usage",
        quantity=quantity,
        note=", ".join(note_parts) if note_parts else "",
    ))
    db.flush()


def grant_bonus_tickets(db: Session, account: Account, quantity: int,
                        granted_by: int | None, note: str = "") -> None:
    """
    Superadmin otorga tickets bonus a una cuenta.
    Los tickets bonus no se resetean mensualmente.
    """
    if account is None or quantity <= 0:
        return

    account.bonus_tickets = (account.bonus_tickets or 0) + quantity

    db.add(TicketQuotaLog(
        account_id=account.id,
        action="grant_bonus",
        quantity=quantity,
        performed_by=granted_by,
        note=note or f"Otorgados {quantity} tickets bonus",
    ))
    db.flush()


def reset_monthly_quotas(db: Session) -> int:
    """
    Tarea programada: resetea contadores mensuales de cuentas vencidas.

    Returns:
        Número de cuentas reseteadas
    """
    now = datetime.utcnow()
    accounts = db.query(Account).filter(
        Account.deleted_at.is_(None),
        Account.ticket_quota_reset_at <= now
    ).all()

    count = 0
    for acc in accounts:
        if acc.tickets_used_this_month > 0:
            db.add(TicketQuotaLog(
                account_id=acc.id,
                action="reset_monthly",
                quantity=acc.tickets_used_this_month,
                note="Reset mensual automático (tarea programada)",
            ))
            count += 1
        acc.tickets_used_this_month = 0
        acc.ticket_quota_reset_at = now + timedelta(days=30)

    if count:
        db.commit()

    return count
