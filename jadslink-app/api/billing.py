"""Lógica de planes: cálculo de uso/costo híbrido y gates de estado de cuenta."""
from sqlalchemy.orm import Session

from .models import Account, SubscriptionPlan, Device

# Estados en los que la cuenta NO puede operar (generar códigos, validar).
BLOCKED_STATUSES = {"suspended", "canceled"}


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
        }

    included = plan.included_devices
    extra = max(0, count - included)
    extra_cost = round(extra * plan.price_per_extra_device_usd, 2)
    total = round(plan.base_price_usd + extra_cost, 2)
    at_limit = plan.max_devices is not None and count >= plan.max_devices

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
    }


def can_add_device(db: Session, account: Account) -> bool:
    """True si la cuenta puede registrar un router más (respeta el tope del plan)."""
    plan = get_plan(db, account.plan) if account else None
    if not plan or plan.max_devices is None:
        return True
    return device_count(db, account.id) < plan.max_devices
