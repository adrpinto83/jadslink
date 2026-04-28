from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join
from sqlalchemy.orm import joinedload
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from models.user import User
from models.tenant import Tenant
from schemas.auth import LoginRequest, TokenResponse, RefreshRequest, RegisterRequest, RegisterResponse, UserResponse
from database import get_db
from config import get_settings
from passlib.context import CryptContext
from utils.rate_limit import rate_limit
import re
from deps import get_current_user

router = APIRouter()
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password using the bcrypt context."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hashes a password using the bcrypt context."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    http_request: Request,
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit(max_requests=5, window_seconds=300, endpoint="auth_register")),
):
    """Register a new operator and their tenant with Free plan active."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un usuario con este email ya existe",
        )

    # Create new tenant with Free plan (auto-activated for demo)
    slug = slugify(request.company_name)
    new_tenant = Tenant(
        name=request.company_name,
        slug=slug,
        is_active=True,  # Auto-activate with Free plan for demo
        plan_tier="free",
        subscription_status="trialing",
        free_tickets_limit=50,  # 50 free demo tickets
        free_tickets_used=0,
    )
    db.add(new_tenant)
    await db.flush()  # Flush to get the new_tenant.id

    # Create new user (operator) as owner of the tenant
    hashed_password = hash_password(request.password)
    new_user = User(
        email=request.email,
        full_name=request.email.split("@")[0],  # Use email prefix as default name
        password_hash=hashed_password,
        role="operator",
        tenant_role="owner",  # First user of a tenant is the owner
        tenant_id=new_tenant.id,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()

    return RegisterResponse(status="success", message="Cuenta creada! Plan Free activado con 50 tickets de demostración. Actualiza tu logo en Settings después de actualizar a un plan pagado.")


@router.post("/login")
async def login(
    http_request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit(max_requests=5, window_seconds=60, endpoint="auth_login")),
):
    """Authenticate user and return JWT access token + refresh token (HttpOnly cookie)"""
    result = await db.execute(
        select(User).options(joinedload(User.tenant)).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )

    if user.role != "superadmin" and (not user.tenant or not user.tenant.is_active):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta del operador no está activa.",
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "role": user.role,
        }
    )
    refresh_token = create_access_token(
        data={"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS),
    )

    # Create response with access token
    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    # Set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 60 * 60,
    )

    return response


@router.post("/refresh")
async def refresh(http_request: Request, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token from HttpOnly cookie"""
    # Get refresh token from cookie
    refresh_token = http_request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco no encontrado",
        )

    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None or payload.get("type") != "refresh":
            raise JWTError("Token inválido")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido",
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "role": user.role,
        }
    )
    new_refresh_token = create_access_token(
        data={"sub": str(user.id), "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS),
    )

    # Create response with new access token
    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    # Set new refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 60 * 60,
    )

    return response


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
