from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Account(Base):
    """Tenant: el operador que paga la suscripción y es dueño de sus routers."""
    __tablename__ = "accounts"

    id            = Column(String, primary_key=True)        # UUID
    name          = Column(String, nullable=False)
    slug          = Column(String, unique=True, nullable=False)
    status        = Column(String, default="active")        # trial|active|past_due|suspended|canceled
    # Suscripción (FASE B/C: SubscriptionPlan y facturación). Placeholders aquí.
    plan          = Column(String, default="trial")         # starter|pro|business|trial
    billing_cycle_end = Column(DateTime, nullable=True)     # hasta cuándo está pagado
    trial_ends_at = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users         = relationship("User",        back_populates="account", cascade="all, delete")
    devices       = relationship("Device",      back_populates="account")
    groups        = relationship("DeviceGroup", back_populates="account", cascade="all, delete")


class DeviceGroup(Base):
    """Agrupa routers de una cuenta (por ruta, flota, zona)."""
    __tablename__ = "device_groups"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    account_id    = Column(String, ForeignKey("accounts.id"), nullable=False)
    name          = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    account       = relationship("Account", back_populates="groups")
    devices       = relationship("Device",  back_populates="group")


class Device(Base):
    __tablename__ = "devices"

    id            = Column(String, primary_key=True)       # UUID generado en registro
    account_id    = Column(String, ForeignKey("accounts.id"), nullable=True)   # dueño (null = huérfano/legacy)
    group_id      = Column(Integer, ForeignKey("device_groups.id"), nullable=True)
    name          = Column(String, nullable=False)
    api_key       = Column(String, unique=True, nullable=False)
    location      = Column(String, default="")
    firmware      = Column(String, default="")
    model         = Column(String, default="OpenWrt")
    last_seen     = Column(DateTime, nullable=True)
    online        = Column(Boolean, default=False)

    # Espejo de persist: configuración activa del dispositivo
    config        = Column(JSON, default=dict)

    account       = relationship("Account", back_populates="devices")
    group         = relationship("DeviceGroup", back_populates="devices")
    clients       = relationship("Client",  back_populates="device", cascade="all, delete")
    codes         = relationship("Code",    back_populates="device", cascade="all, delete")
    reports       = relationship("Report",  back_populates="device", cascade="all, delete")
    commands      = relationship("Command", back_populates="device", cascade="all, delete")
    created_at    = Column(DateTime, default=datetime.utcnow)


class Client(Base):
    __tablename__ = "clients"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    device_id     = Column(String, ForeignKey("devices.id"), nullable=False)
    mac           = Column(String, nullable=False)
    ip            = Column(String, default="")
    hostname      = Column(String, default="")
    bytes_in      = Column(Integer, default=0)
    bytes_out     = Column(Integer, default=0)
    connected_at  = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime, nullable=True)
    active        = Column(Boolean, default=True)
    code_used     = Column(String, default="")

    device        = relationship("Device", back_populates="clients")


class Code(Base):
    __tablename__ = "codes"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    device_id     = Column(String, ForeignKey("devices.id"), nullable=False)
    code          = Column(String, nullable=False)
    duration_min  = Column(Integer, default=60)     # minutos de acceso
    max_uses      = Column(Integer, default=1)
    uses          = Column(Integer, default=0)
    bandwidth_dn  = Column(Integer, default=0)      # kbps, 0=ilimitado
    bandwidth_up  = Column(Integer, default=0)
    expires_at    = Column(DateTime, nullable=True)
    active        = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    note          = Column(String, default="")

    device        = relationship("Device", back_populates="codes")


class Report(Base):
    __tablename__ = "reports"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    device_id     = Column(String, ForeignKey("devices.id"), nullable=False)
    timestamp     = Column(DateTime, default=datetime.utcnow)
    clients_count = Column(Integer, default=0)
    bytes_in      = Column(Integer, default=0)
    bytes_out     = Column(Integer, default=0)
    cpu_load      = Column(Float, default=0.0)
    mem_free_mb   = Column(Float, default=0.0)
    uptime_sec    = Column(Integer, default=0)
    wan_ip        = Column(String, default="")

    device        = relationship("Device", back_populates="reports")


class Command(Base):
    __tablename__ = "commands"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    device_id     = Column(String, ForeignKey("devices.id"), nullable=False)
    action        = Column(String, nullable=False)  # reboot, update_config, kick_client, etc.
    payload       = Column(JSON, default=dict)
    status        = Column(String, default="pending")   # pending, delivered, done, error
    created_at    = Column(DateTime, default=datetime.utcnow)
    delivered_at  = Column(DateTime, nullable=True)
    done_at       = Column(DateTime, nullable=True)
    result        = Column(Text, default="")

    device        = relationship("Device", back_populates="commands")


class AdminUser(Base):
    # LEGACY: se mantiene por compatibilidad de datos. El login usa `User`.
    __tablename__ = "admin_users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """Usuario del panel. Pertenece a una cuenta (o account_id=NULL si es superadmin)."""
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    account_id    = Column(String, ForeignKey("accounts.id"), nullable=True)   # NULL = superadmin JADS
    username      = Column(String, unique=True, nullable=False)                # handle de login
    email         = Column(String, default="")
    password_hash = Column(String, nullable=False)
    full_name     = Column(String, default="")
    role          = Column(String, default="owner")   # superadmin|owner|manager|viewer
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    account       = relationship("Account", back_populates="users")


class Settings(Base):
    __tablename__ = "settings"

    key   = Column(String, primary_key=True)
    value = Column(String, default="")
