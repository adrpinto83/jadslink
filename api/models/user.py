from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel, Base
import uuid
import enum
from typing import Optional


class UserRole(str, enum.Enum):
    """Roles globales del sistema"""
    superadmin = "superadmin"    # Administrador de la plataforma JADSlink
    operator = "operator"        # Usuario de una cuenta/tenant


class TenantRole(str, enum.Enum):
    """Roles dentro de un tenant (cuenta)"""
    owner = "owner"              # Dueño de la cuenta (quien la creó)
    admin = "admin"              # Administrador con permisos de gestión
    collaborator = "collaborator"  # Colaborador con acceso de lectura/escritura limitado
    viewer = "viewer"            # Solo lectura


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Rol global en la plataforma
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.operator, nullable=False
    )

    # Rol dentro del tenant (si aplica)
    tenant_role: Mapped[Optional[TenantRole]] = mapped_column(
        SQLEnum(TenantRole), default=TenantRole.owner, nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Asociación con tenant
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant", back_populates="users", foreign_keys=[tenant_id]
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
