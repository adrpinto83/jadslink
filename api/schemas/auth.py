from pydantic import BaseModel, EmailStr
from uuid import UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    company_name: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterResponse(BaseModel):
    status: str
    message: str | None = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    tenant_id: UUID | None = None

    class Config:
        from_attributes = True
