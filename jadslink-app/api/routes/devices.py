from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
import uuid, secrets, os

from ..database import get_db
from ..models import Device, Report, Command, Client, Code, Account, User
from .auth import require_user
from ..scope import scope_devices, owned_device, is_superadmin
from .. import billing

router = APIRouter(prefix="/api/devices", tags=["devices"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class DeviceRegister(BaseModel):
    name: str
    location: str = ""
    model: str = "OpenWrt"
    account_id: Optional[str] = None   # solo superadmin puede fijarlo
    group_id: Optional[int] = None

class HeartbeatPayload(BaseModel):
    firmware: str = ""
    wan_ip: str = ""
    clients_count: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    cpu_load: float = 0.0
    mem_free_mb: float = 0.0
    uptime_sec: int = 0
    clients: list[dict] = []

class ConfigUpdate(BaseModel):
    config: dict

class SsidUpdate(BaseModel):
    ssid: str

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    group_id: Optional[int] = None

class CommandResult(BaseModel):
    command_id: int
    status: str       # done | error
    result: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_device_by_key(api_key: str, db: Session) -> Device:
    device = db.query(Device).filter(Device.api_key == api_key).first()
    if not device:
        raise HTTPException(status_code=401, detail="API key inválida")
    return device

def require_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    return get_device_by_key(x_api_key, db)

def _resolve_account_id(payload_account_id: Optional[str], user: User, db: Session) -> Optional[str]:
    """Determina la cuenta destino de un device nuevo respetando permisos."""
    if is_superadmin(user):
        if payload_account_id:
            return payload_account_id
        # superadmin sin cuenta explícita → cuenta por defecto
        from ..migrate import DEFAULT_ACCOUNT_SLUG
        acc = db.query(Account).filter(Account.slug == DEFAULT_ACCOUNT_SLUG).first()
        return acc.id if acc else None
    # operador: siempre su propia cuenta
    return user.account_id


# ── Registro ──────────────────────────────────────────────────────────────────

@router.post("/register")
def register_device(payload: DeviceRegister, db: Session = Depends(get_db), user: User = Depends(require_user)):
    account_id = _resolve_account_id(payload.account_id, user, db)
    # Límite de routers del plan (el superadmin puede exceder; él gestiona el cobro).
    if not is_superadmin(user):
        acc = db.query(Account).filter(Account.id == account_id).first()
        if acc and billing.account_blocked(acc):
            raise HTTPException(status_code=403, detail="Cuenta suspendida")
        if acc and not billing.can_add_device(db, acc):
            raise HTTPException(status_code=403, detail="Alcanzaste el límite de routers de tu plan. Mejora tu plan para agregar más.")
    device = Device(
        id=str(uuid.uuid4()),
        account_id=account_id,
        group_id=payload.group_id,
        name=payload.name,
        location=payload.location,
        model=payload.model,
        api_key=secrets.token_urlsafe(32),
        config={},
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return {"device_id": device.id, "api_key": device.api_key}


# ── Heartbeat (dispositivo → nube) ────────────────────────────────────────────

@router.post("/{device_id}/heartbeat")
def heartbeat(
    device_id: str,
    payload: HeartbeatPayload,
    device: Device = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    if device.id != device_id:
        raise HTTPException(status_code=403)

    device.last_seen = datetime.utcnow()
    device.online = True
    device.firmware = payload.firmware or device.firmware
    device.wan_ip = payload.wan_ip  # type: ignore[attr-defined]

    # Guardar snapshot de métricas
    report = Report(
        device_id=device.id,
        clients_count=payload.clients_count,
        bytes_in=payload.bytes_in,
        bytes_out=payload.bytes_out,
        cpu_load=payload.cpu_load,
        mem_free_mb=payload.mem_free_mb,
        uptime_sec=payload.uptime_sec,
        wan_ip=payload.wan_ip,
    )
    db.add(report)

    # Sincronizar clientes activos: primero marcar todos como desconectados,
    # luego reactivar los que siguen en la lista. Así si llega lista vacía
    # los clientes se marcan offline correctamente.
    db.query(Client).filter(
        Client.device_id == device.id,
        Client.active == True,
    ).update({"active": False, "disconnected_at": datetime.utcnow()})

    for c in payload.clients:
        existing = db.query(Client).filter(
            Client.device_id == device.id,
            Client.mac == c.get("mac"),
            Client.active == False,
            Client.disconnected_at >= datetime.utcnow() - timedelta(minutes=5)
        ).first()
        if existing:
            existing.active = True
            existing.disconnected_at = None
            existing.bytes_in = c.get("bytes_in", 0)
            existing.bytes_out = c.get("bytes_out", 0)
            if c.get("code_used"):
                existing.code_used = c["code_used"]
        else:
            db.add(Client(
                device_id=device.id,
                mac=c.get("mac", ""),
                ip=c.get("ip", ""),
                hostname=c.get("hostname", ""),
                bytes_in=c.get("bytes_in", 0),
                bytes_out=c.get("bytes_out", 0),
                code_used=c.get("code_used", ""),
            ))

    db.commit()

    # Devolver comandos pendientes
    pending = db.query(Command).filter(
        Command.device_id == device.id,
        Command.status == "pending"
    ).all()

    cmds = [{"id": c.id, "action": c.action, "payload": c.payload} for c in pending]
    for c in pending:
        c.status = "delivered"
        c.delivered_at = datetime.utcnow()
    db.commit()

    return {"commands": cmds}


# ── Resultado de comando ──────────────────────────────────────────────────────

@router.post("/{device_id}/command-result")
def command_result(
    device_id: str,
    payload: CommandResult,
    device: Device = Depends(require_api_key),
    db: Session = Depends(get_db),
):
    cmd = db.query(Command).filter(
        Command.id == payload.command_id,
        Command.device_id == device.id,
    ).first()
    if not cmd:
        raise HTTPException(status_code=404)
    cmd.status = payload.status
    cmd.result = payload.result
    cmd.done_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


# ── Admin: resumen ────────────────────────────────────────────────────────────

@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(require_user)):
    now = datetime.utcnow()
    all_devices = scope_devices(db.query(Device), user).all()
    for d in all_devices:
        if d.last_seen and (now - d.last_seen).total_seconds() > 120:
            d.online = False
    db.commit()
    online = sum(1 for d in all_devices if d.online)
    device_ids = [d.id for d in all_devices]

    if device_ids:
        active_clients = db.query(Client).filter(
            Client.device_id.in_(device_ids), Client.active == True
        ).count()
        active_codes = db.query(Code).filter(
            Code.device_id.in_(device_ids), Code.active == True
        ).count()
        recent = (db.query(Client, Device.name)
                  .join(Device, Client.device_id == Device.id)
                  .filter(Client.device_id.in_(device_ids))
                  .order_by(Client.connected_at.desc()).limit(20).all())
    else:
        active_clients, active_codes, recent = 0, 0, []

    return {
        "devices_total": len(all_devices),
        "devices_online": online,
        "active_clients": active_clients,
        "active_codes": active_codes,
        "recent_connections": [{
            "device_name": name,
            "mac": c.mac, "ip": c.ip, "code_used": c.code_used,
            "connected_at": c.connected_at.isoformat(),
            "active": c.active,
        } for c, name in recent],
    }


# ── Admin: listar dispositivos ────────────────────────────────────────────────

@router.get("")
def list_devices(db: Session = Depends(get_db), user: User = Depends(require_user)):
    devices = scope_devices(db.query(Device), user).all()
    now = datetime.utcnow()
    result = []
    for d in devices:
        if d.last_seen and (now - d.last_seen).total_seconds() > 120:
            d.online = False
        active_clients = db.query(Client).filter(
            Client.device_id == d.id, Client.active == True
        ).count()
        result.append({
            "id": d.id,
            "name": d.name,
            "location": d.location,
            "model": d.model,
            "online": d.online,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "firmware": d.firmware,
            "config": d.config,
            "api_key": d.api_key,
            "account_id": d.account_id,
            "group_id": d.group_id,
            "active_clients": active_clients,
        })
    db.commit()
    return result


@router.get("/{device_id}")
def get_device(device_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    d = owned_device(device_id, user, db)
    return {
        "id": d.id, "name": d.name, "location": d.location,
        "model": d.model, "online": d.online, "firmware": d.firmware,
        "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        "config": d.config, "api_key": d.api_key,
        "account_id": d.account_id, "group_id": d.group_id,
    }


@router.get("/{device_id}/onboarding")
def onboarding(device_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Datos para dar de alta el router: agent.conf listo + pasos de instalación."""
    d = owned_device(device_id, user, db)
    cloud_url = os.getenv("PUBLIC_URL", "https://link.jadsstudio.com")
    agent_conf = (
        f'DEVICE_ID="{d.id}"\n'
        f'API_KEY="{d.api_key}"\n'
        f'CLOUD_URL="{cloud_url}"\n'
        f'INTERVAL=30\n'
    )
    steps = [
        {"title": "1. Conéctate al router por SSH",
         "detail": "ssh root@192.168.8.1  (o la IP LAN de tu GL.iNet/OpenWrt)"},
        {"title": "2. Crea el archivo de configuración del agente",
         "detail": "Pega el contenido de abajo en /etc/hotspot/agent.conf"},
        {"title": "3. Instala y arranca el agente",
         "detail": "sh <(wget -qO- " + cloud_url + "/static/agent/install.sh)"},
        {"title": "4. Verifica",
         "detail": "El router aparecerá en línea en el panel en ~30 segundos."},
    ]
    return {
        "device_id": d.id, "api_key": d.api_key, "cloud_url": cloud_url,
        "agent_conf": agent_conf, "steps": steps,
    }


@router.patch("/{device_id}")
def update_device(device_id: str, payload: DeviceUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    d = owned_device(device_id, user, db)
    if payload.name is not None:
        d.name = payload.name
    if payload.location is not None:
        d.location = payload.location
    if payload.group_id is not None:
        d.group_id = payload.group_id or None
    db.commit()
    return {"ok": True}


@router.put("/{device_id}/config")
def update_config(device_id: str, payload: ConfigUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    d = owned_device(device_id, user, db)
    d.config = {**(d.config or {}), **payload.config}
    db.add(Command(device_id=d.id, action="update_config", payload=payload.config))
    db.commit()
    return {"ok": True}


@router.post("/{device_id}/reboot")
def reboot_device(device_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    d = owned_device(device_id, user, db)
    db.add(Command(device_id=d.id, action="reboot", payload={}))
    db.commit()
    return {"ok": True}


@router.post("/{device_id}/ssid")
def set_ssid(device_id: str, payload: SsidUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    d = owned_device(device_id, user, db)
    ssid = payload.ssid.strip()
    if not ssid or len(ssid) > 32:
        raise HTTPException(status_code=400, detail="SSID debe tener entre 1 y 32 caracteres")
    d.config = {**(d.config or {}), "wlan.essid": ssid}
    db.add(Command(device_id=d.id, action="set_ssid", payload={"ssid": ssid}))
    db.commit()
    return {"ok": True}


@router.get("/{device_id}/clients")
def get_clients(device_id: str, active_only: bool = True, db: Session = Depends(get_db), user: User = Depends(require_user)):
    owned_device(device_id, user, db)
    q = db.query(Client).filter(Client.device_id == device_id)
    if active_only:
        q = q.filter(Client.active == True)
    clients = q.order_by(Client.connected_at.desc()).limit(500).all()
    return [{
        "id": c.id, "mac": c.mac, "ip": c.ip, "hostname": c.hostname,
        "bytes_in": c.bytes_in, "bytes_out": c.bytes_out,
        "connected_at": c.connected_at.isoformat(),
        "active": c.active, "code_used": c.code_used,
    } for c in clients]


@router.post("/{device_id}/kick/{mac}")
def kick_client(device_id: str, mac: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    d = owned_device(device_id, user, db)
    db.add(Command(device_id=d.id, action="kick_client", payload={"mac": mac}))
    db.commit()
    return {"ok": True}


@router.get("/{device_id}/logs")
def get_logs(device_id: str, limit: int = 200, days: int = 28, db: Session = Depends(get_db), user: User = Depends(require_user)):
    owned_device(device_id, user, db)
    since = datetime.utcnow() - timedelta(days=days)
    clients = (db.query(Client)
               .filter(Client.device_id == device_id, Client.connected_at >= since)
               .order_by(Client.connected_at.desc()).limit(limit).all())
    return [{
        "id": c.id, "mac": c.mac, "ip": c.ip, "hostname": c.hostname,
        "bytes_in": c.bytes_in, "bytes_out": c.bytes_out,
        "connected_at": c.connected_at.isoformat(),
        "disconnected_at": c.disconnected_at.isoformat() if c.disconnected_at else None,
        "active": c.active, "code_used": c.code_used,
    } for c in clients]


@router.delete("/{device_id}")
def delete_device(device_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    d = owned_device(device_id, user, db)
    db.delete(d)
    db.commit()
    return {"ok": True}


@router.get("/{device_id}/usage-summary")
def usage_summary(device_id: str, days: int = 30, db: Session = Depends(get_db), user: User = Depends(require_user)):
    owned_device(device_id, user, db)
    total_codes  = db.query(Code).filter(Code.device_id == device_id).count()
    active_codes = db.query(Code).filter(Code.device_id == device_id, Code.active == True).count()
    used_codes   = db.query(Code).filter(Code.device_id == device_id, Code.uses > 0).count()

    total_clients = db.query(Client).filter(Client.device_id == device_id).count()
    bytes_in  = db.query(func.sum(Client.bytes_in)).filter(Client.device_id == device_id).scalar() or 0
    bytes_out = db.query(func.sum(Client.bytes_out)).filter(Client.device_id == device_id).scalar() or 0

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    daily = []
    for i in range(days - 1, -1, -1):
        d_start = today - timedelta(days=i)
        d_end   = d_start + timedelta(days=1)
        count = db.query(Client).filter(
            Client.device_id == device_id,
            Client.connected_at >= d_start,
            Client.connected_at <  d_end,
        ).count()
        daily.append({"date": d_start.strftime("%-d/%m"), "connections": count})

    return {
        "codes":   {"total": total_codes, "active": active_codes, "used": used_codes},
        "clients": {"total": total_clients, "bytes_in": bytes_in, "bytes_out": bytes_out},
        "daily":   daily,
    }


@router.get("/{device_id}/reports")
def get_reports(device_id: str, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(require_user)):
    owned_device(device_id, user, db)
    reports = db.query(Report).filter(Report.device_id == device_id)\
                .order_by(Report.timestamp.desc()).limit(limit).all()
    return [{
        "timestamp": r.timestamp.isoformat(),
        "clients_count": r.clients_count,
        "bytes_in": r.bytes_in, "bytes_out": r.bytes_out,
        "cpu_load": r.cpu_load, "mem_free_mb": r.mem_free_mb,
        "uptime_sec": r.uptime_sec, "wan_ip": r.wan_ip,
    } for r in reports]


# ── Seed: dispositivos conocidos (agentes en campo) ───────────────────────────
# Reinsertados en cada arranque para sobrevivir recreaciones de la BD SQLite.
# Sin esto, un redeploy borra la fila del agente del router y su device_id/api_key
# quedan huérfanos -> heartbeat 401 -> dispositivo offline.
SEED_DEVICES = [
    {
        "id": "e4916825-74af-42ac-b3dc-ba26e4647e19",
        "name": "Router Hotspot Principal",
        "api_key": "Pysp-zQZE3h230DhEALCAkOTpqZ3d3tjOGkpyl_axoI",
        "location": "Lobby",
        "model": "OpenWrt 23.05.3",
        "firmware": "OpenWrt 23.05.3",
    },
]


def seed_devices(db: Session):
    """Garantiza que los agentes conocidos existan con su api_key correcta.

    El backfill de cuenta (account_id) lo hace run_data_migrations tras este seed.
    """
    for spec in SEED_DEVICES:
        d = db.query(Device).filter(Device.id == spec["id"]).first()
        if d is None:
            db.add(Device(
                id=spec["id"], name=spec["name"], api_key=spec["api_key"],
                location=spec.get("location", ""), model=spec.get("model", "OpenWrt"),
                firmware=spec.get("firmware", ""), config={},
            ))
        elif d.api_key != spec["api_key"]:
            d.api_key = spec["api_key"]
    db.commit()
