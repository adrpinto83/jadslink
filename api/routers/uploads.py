"""Routes for file uploads (payment receipts, comprobantes)."""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from services.storage_service import StorageService
import logging

log = logging.getLogger("jadslink.uploads")

router = APIRouter()


@router.post("/comprobante")
async def upload_comprobante(
    file: UploadFile = File(...),
):
    """
    Upload payment receipt file (PNG, JPG, PDF).
    Max size: 5MB.

    Returns:
        {
            "success": true,
            "url": "/uploads/comprobantes/20260426_123456_abc12345.jpg",
            "filename": "comprobante.png"
        }
    """
    try:
        # Read file contents
        contents = await file.read()

        # Upload to local storage
        success, result = await StorageService.upload_comprobante(contents, file.filename or "comprobante")

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result,  # error message
            )

        log.info(f"Comprobante uploaded: {file.filename} -> {result}")

        return {
            "success": True,
            "url": result,
            "filename": file.filename,
            "message": "Comprobante subido exitosamente",
        }

    except Exception as e:
        log.error(f"Error uploading comprobante: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar la carga del archivo",
        )
