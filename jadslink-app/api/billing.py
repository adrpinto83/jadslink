"""Lógica de planes: cálculo de uso/costo híbrido, gates de estado y ciclo de facturación."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .models import Account, SubscriptionPlan, Device

# Estados en los que la cuenta NO puede operar (generar códigos, validar).
BLOCKED_STATUSES = {"suspended", "canceled"}

CYCLE_DAYS = 30   # duración de un ciclo pagado
GRACE_DAYS = 5    # días de gracia tras el vencimiento antes de suspender
TRIAL_DAYS = 14   # duración del trial


def billing_info(account: Account) -> dict:
    """Estado de facturación: cuándo vence y días restantes."""
    end = account.billing_cycle_end if account else None
    if end is None:
        return {"billing_cycle_end": None, "days_left": None, "expired": False, "grace": False}
    now = datetime.utcnow()
    delta = end - now
    days_left = delta.days if delta.total_seconds() >= 0 else -((-delta).days + (1 if (-delta).seconds else 0))
    return {
        "billing_cycle_end": end.isoformat(),
        "days_left": days_left,
        "expired": now > end,
        "grace": end < now <= end + timedelta(days=GRACE_DAYS),
    }


def init_billing_for_new_account(account: Account, plan_key: str) -> None:
    """Fija fechas iniciales al crear la cuenta según el plan."""
    now = datetime.utcnow()
    if plan_key == "trial":
        account.trial_ends_at = now + timedelta(days=TRIAL_DAYS)
        account.billing_cycle_end = account.trial_ends_at
        account.status = "trial"
    else:
        # Primer ciclo de cortesía; el operador reporta su pago dentro del periodo.
        account.billing_cycle_end = now + timedelta(days=CYCLE_DAYS)
        account.status = "active"


def approve_and_extend(account: Account, days: int = CYCLE_DAYS) -> tuple:
    """Extiende el ciclo pagado y reactiva la cuenta. Devuelve (inicio, fin)."""
    now = datetime.utcnow()
    base = account.billing_cycle_end if (account.billing_cycle_end and account.billing_cycle_end > now) else now
    account.billing_cycle_end = base + timedelta(days=days)
    account.status = "active"
    return base, account.billing_cycle_end


def run_billing_cycle(db: Session) -> int:
    """Marca cuentas vencidas como past_due y, pasada la gracia, suspended.

    Cuentas con billing_cycle_end = NULL nunca vencen (p. ej. la cuenta JADS Studio).
    Devuelve cuántas cuentas cambiaron de estado.
    """
    now = datetime.utcnow()
    accts = (db.query(Account)
             .filter(Account.billing_cycle_end.isnot(None),
                     Account.status.in_(["active", "trial", "past_due"]))
             .all())
    changed = 0
    for a in accts:
        if now > a.billing_cycle_end + timedelta(days=GRACE_DAYS):
            if a.status != "suspended":
                a.status = "suspended"; changed += 1
        elif now > a.billing_cycle_end:
            if a.status != "past_due":
                a.status = "past_due"; changed += 1
    if changed:
        db.commit()
    return changed


def get_plan(db: Session, plan_key: str) -> SubscriptionPlan | None:
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.key == plan_key).first()


def account_blocked(account: Account) -> bool:
    return account is not None and account.status in BLOCKED_STATUSES


def device_count(db: Session, account_id: str) -> int:
    return db.query(Device).filter(Device.account_id == account_id).count()


def compute_usage(db: Session, account: Account) -> dict:
    """Uso y costo mensual estimado de una cuenta según su plan (cobro híbrido)."""
    plan = get_plan(db, account.plan) if account else None
    count = device_count(db, account.id) if account else 0

    if not plan:
        return {
            "plan": account.plan if account else None, "plan_name": account.plan if account else None,
            "device_count": count, "included_devices": None, "max_devices": None,
            "extra_devices": 0, "base_price": 0.0, "extra_cost": 0.0, "total_monthly": 0.0,
            "at_limit": False,
            "tickets_per_month": 0, "tickets_used": 0, "tickets_bonus": 0, "tickets_unlimited": True,
        }

    included = plan.included_devices
    extra = max(0, count - included)
    extra_cost = round(extra * plan.price_per_extra_device_usd, 2)
    total = round(plan.base_price_usd + extra_cost, 2)
    at_limit = plan.max_devices is not None and count >= plan.max_devices

    # Cuotas de tickets
    tickets_per_month = plan.tickets_per_month if hasattr(plan, 'tickets_per_month') else 0
    tickets_used = account.tickets_used_this_month if account else 0
    tickets_bonus = account.bonus_tickets if account else 0
    tickets_unlimited = tickets_per_month == 0

    return {
        "plan": plan.key,
        "plan_name": plan.name,
        "device_count": count,
        "included_devices": included,
        "max_devices": plan.max_devices,
        "extra_devices": extra,
        "base_price": plan.base_price_usd,
        "price_per_extra_device": plan.price_per_extra_device_usd,
        "extra_cost": extra_cost,
        "total_monthly": total,
        "at_limit": at_limit,
        "tickets_per_month": tickets_per_month,
        "tickets_used": tickets_used or 0,
        "tickets_bonus": tickets_bonus or 0,
        "tickets_unlimited": tickets_unlimited,
    }


def can_add_device(db: Session, account: Account) -> bool:
    """True si la cuenta puede registrar un router más (respeta el tope del plan)."""
    plan = get_plan(db, account.plan) if account else None
    if not plan or plan.max_devices is None:
        return True
    return device_count(db, account.id) < plan.max_devices
