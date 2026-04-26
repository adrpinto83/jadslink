from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from pathlib import Path
import aiofiles
import imghdr

from database import get_db
from config import get_settings
from models.tenant import Tenant
from schemas.tenant import TenantResponse
from deps import get_superadmin
from models.user import User
from services.subscription_service import create_stripe_customer

router = APIRouter()
settings = get_settings()


@router.patch("/tenants/{tenant_id}/approve", response_model=TenantResponse)
async def approve_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    superadmin: User = Depends(get_superadmin)
):
    """Approve a tenant, setting them to active."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    if tenant.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ya está activo")

    tenant.is_active = True
    await create_stripe_customer(tenant, db) # Create Stripe customer
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return tenant


@router.post("/logo")
async def upload_app_logo(
    file: UploadFile = File(...),
    superadmin: User = Depends(get_superadmin),
):
    """
    Upload JADSlink application logo (admin only).
    This logo appears in all parts of the app where "JADSlink" appears.
    """
    # Validate file type
    if not file.filename or not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo inválido"
        )

    # Read file content
    content = await file.read()

    # Validate file size (max 5MB)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Archivo demasiado grande (máximo 5MB)"
        )

    # Validate image type
    image_type = imghdr.what(None, h=content)
    if image_type not in ["jpeg", "png", "gif", "webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan imágenes (JPEG, PNG, GIF, WebP)"
        )

    # Create uploads/app directory if it doesn't exist
    uploads_dir = Path("uploads/app")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename for JADSlink logo (fixed name, replaces existing)
    file_extension = imghdr.what(None, h=content)
    filename = f"jadslink.{file_extension}"
    file_path = uploads_dir / filename

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    logo_url = f"{settings.API_BASE_URL}/uploads/app/{filename}"

    return {
        "status": "success",
        "message": "Logo de JADSlink actualizado exitosamente",
        "logo_url": logo_url
    }


@router.get("/logo/public")
async def get_app_logo_public():
    """
    Get JADSlink application logo (public endpoint, no authentication required).
    Used for displaying logo in login/register and throughout the app.
    """
    # Check if logo exists
    uploads_dir = Path("uploads/app")
    logo_files = list(uploads_dir.glob("jadslink.*"))

    if logo_files:
        # Logo exists, return its URL
        logo_filename = logo_files[0].name
        logo_url = f"{settings.API_BASE_URL}/uploads/app/{logo_filename}"
        return {
            "logo_url": logo_url,
            "has_custom_logo": True
        }
    else:
        # No custom logo, return null
        return {
            "logo_url": None,
            "has_custom_logo": False
        }
