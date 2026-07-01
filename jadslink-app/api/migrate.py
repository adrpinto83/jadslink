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

from .models import Account, Device, User, AdminUser

DEFAULT_ACCOUNT_SLUG = "jads-studio"
DEFAULT_ACCOUNT_NAME = "JADS Studio"


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
    """Siembra cuenta por defecto, superadmin y hace backfill de devices."""
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
