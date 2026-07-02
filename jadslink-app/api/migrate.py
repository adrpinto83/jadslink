"""Migraciones idempotentes para SQLite/Postgres sin Alembic.

`Base.metadata.create_all` crea tablas nuevas pero NO agrega columnas a tablas
existentes. Este módulo agrega las columnas faltantes con ALTER TABLE y siembra
los datos base (cuenta por defecto, superadmin, backfill de devices).

Se ejecuta en cada arranque (lifespan). Todo es idempotente y seguro de repetir.
"""
import uuid
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .models import Account, Device, User, AdminUser, SubscriptionPlan

DEFAULT_ACCOUNT_SLUG = "jads-studio"
DEFAULT_ACCOUNT_NAME = "JADS Studio"

# Catálogo de planes (cobro híbrido: base + extra por router). Ver SUBSCRIPTION_PLAN.md.
PLAN_CATALOG = [
    {"key": "trial",    "name": "Trial",    "base_price_usd": 0.0,  "included_devices": 1,
     "price_per_extra_device_usd": 0.0, "max_devices": 1,    "sort_order": 0,
     "features": {"trial_days": 14}},
    {"key": "starter",  "name": "Starter",  "base_price_usd": 15.0, "included_devices": 2,
     "price_per_extra_device_usd": 6.0, "max_devices": 5,    "sort_order": 1,
     "features": {"reports": True, "portal_branding": True}},
    {"key": "pro",      "name": "Pro",      "base_price_usd": 29.0, "included_devices": 5,
     "price_per_extra_device_usd": 5.0, "max_devices": 20,   "sort_order": 2,
     "features": {"reports": True, "portal_branding": True, "groups": True, "multi_user": True}},
    {"key": "business", "name": "Business", "base_price_usd": 79.0, "included_devices": 15,
     "price_per_extra_device_usd": 4.0, "max_devices": None, "sort_order": 3,
     "features": {"reports": True, "portal_branding": True, "groups": True, "multi_user": True,
                  "whitelabel": True, "api": True}},
]


def seed_plans(db: Session) -> None:
    """Crea/actualiza el catálogo de planes (idempotente)."""
    for spec in PLAN_CATALOG:
        p = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == spec["key"]).first()
        if p is None:
            db.add(SubscriptionPlan(**spec))
        else:
            # Mantener precios/límites al día con el catálogo del código.
            for field, val in spec.items():
                setattr(p, field, val)
    db.commit()


def _existing_columns(engine: Engine, table: str) -> set[str]:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def _add_column(engine: Engine, table: str, coldef: str) -> None:
    """ALTER TABLE ... ADD COLUMN. Funciona en SQLite y Postgres."""
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {coldef}"))


def run_schema_migrations(engine: Engine) -> None:
    """Agrega columnas nuevas a tablas preexistentes."""
    dev_cols = _existing_columns(engine, "devices")
    if dev_cols:  # la tabla ya existe (BD con datos previos)
        if "account_id" not in dev_cols:
            _add_column(engine, "devices", "account_id VARCHAR")
        if "group_id" not in dev_cols:
            _add_column(engine, "devices", "group_id INTEGER")
        if "wan_ip" not in dev_cols:
            _add_column(engine, "devices", "wan_ip VARCHAR DEFAULT ''")

    acc_cols = _existing_columns(engine, "accounts")
    if acc_cols and "contact_phone" not in acc_cols:
        _add_column(engine, "accounts", "contact_phone VARCHAR DEFAULT ''")
    if acc_cols and "payment_methods" not in acc_cols:
        _add_column(engine, "accounts", "payment_methods JSON")

    # Índices para las consultas calientes (validate, listados, retención).
    # CREATE INDEX IF NOT EXISTS funciona en SQLite y Postgres.
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_codes_device_code ON codes (device_id, code)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_clients_device_active ON clients (device_id, active)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_reports_device_ts ON reports (device_id, timestamp)"))
        insp = inspect(engine)
        if "code_orders" in insp.get_table_names():
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_account_status ON code_orders (account_id, status)"))


def _get_or_create_default_account(db: Session) -> Account:
    acc = db.query(Account).filter(Account.slug == DEFAULT_ACCOUNT_SLUG).first()
    if acc is None:
        acc = Account(
            id=str(uuid.uuid4()),
            name=DEFAULT_ACCOUNT_NAME,
            slug=DEFAULT_ACCOUNT_SLUG,
            status="active",
            plan="business",
        )
        db.add(acc)
        db.commit()
        db.refresh(acc)
    return acc


def run_data_migrations(db: Session, admin_password: str, hash_pw) -> None:
    """Siembra planes, cuenta por defecto, superadmin y hace backfill de devices."""
    seed_plans(db)
    default_account = _get_or_create_default_account(db)

    # 1. Superadmin: migrar desde AdminUser legacy, o crear admin/ADMIN_PASSWORD.
    if db.query(User).count() == 0:
        legacy = db.query(AdminUser).first()
        if legacy is not None:
            db.add(User(
                username=legacy.username,
                password_hash=legacy.password_hash,
                role="superadmin",
                account_id=None,
                full_name="Administrador",
            ))
        else:
            db.add(User(
                username="admin",
                password_hash=hash_pw(admin_password),
                role="superadmin",
                account_id=None,
                full_name="Administrador",
            ))
        db.commit()

    # 2. Backfill: devices sin cuenta → cuenta por defecto.
    orphans = db.query(Device).filter(Device.account_id.is_(None)).all()
    for d in orphans:
        d.account_id = default_account.id
    if orphans:
        db.commit()
