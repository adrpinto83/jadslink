"""Schemas for user and employee management."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class TenantRoleEnum(str, Enum):
    """Roles dentro de un tenant"""
    owner = "owner"
    admin = "admin"
    collaborator = "collaborator"
    viewer = "viewer"


class UserCreateRequest(BaseModel):
    """Crear un nuevo usuario para un tenant"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    tenant_role: TenantRoleEnum = TenantRoleEnum.collaborator
    password: Optional[str] = None  # Si es None, enviar email de invitación


class UserUpdate(BaseModel):
    """Actualizar información de un usuario"""
    full_name: Optional[str] = None
    tenant_role: Optional[TenantRoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Respuesta de usuario"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str  # Rol global: superadmin, operator
    tenant_role: Optional[str] = None  # Rol en el tenant: owner, admin, collaborator, viewer
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    """Información de un miembro del equipo (para listar)"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    tenant_role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    """Respuesta al listar empleados"""
    members: list[TeamMemberResponse]
    total_count: int
    role_counts: dict[str, int]  # Ej: {"owner": 1, "admin": 2, "collaborator": 5, "viewer": 0}


class InviteUserRequest(BaseModel):
    """Invitar a un usuario a un tenant"""
    email: EmailStr
    full_name: Optional[str] = None
    tenant_role: TenantRoleEnum = TenantRoleEnum.collaborator


class ChangeRoleRequest(BaseModel):
    """Cambiar rol de un usuario"""
    tenant_role: TenantRoleEnum


class RemoveUserRequest(BaseModel):
    """Remover usuario de un tenant"""
    reason: Optional[str] = None
