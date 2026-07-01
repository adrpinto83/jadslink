"""Helpers de aislamiento multi-tenant.

Toda consulta de recursos (devices, codes, clients, ...) debe filtrarse por la
cuenta del usuario, excepto para superadmin que ve todo.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session, Query

from .models import Device, User


def is_superadmin(user: User) -> bool:
    return user.role == "superadmin"


def scope_devices(query: Query, user: User) -> Query:
    """Filtra un query de Device por la cuenta del usuario (superadmin ve todo)."""
    if is_superadmin(user):
        return query
    return query.filter(Device.account_id == user.account_id)


def owned_device(device_id: str, user: User, db: Session) -> Device:
    """Devuelve el device si el usuario puede verlo; 404 si no existe o no es suyo."""
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    if not is_superadmin(user) and d.account_id != user.account_id:
        # 404 en vez de 403 para no revelar la existencia de recursos ajenos
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return d
