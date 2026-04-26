"""Service for handling file uploads (local storage)."""

from pathlib import Path
from uuid import uuid4
from datetime import datetime
import logging

log = logging.getLogger("jadslink.storage")

# Upload directory for comprobantes
UPLOADS_BASE_DIR = Path("uploads")
COMPROBANTES_DIR = UPLOADS_BASE_DIR / "comprobantes"

# Ensure directories exist
COMPROBANTES_DIR.mkdir(parents=True, exist_ok=True)


class StorageService:
    """Service for managing file uploads locally"""

    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    @staticmethod
    async def upload_comprobante(file_data: bytes, filename: str) -> tuple[bool, str]:
        """
        Upload payment receipt file locally.

        Args:
            file_data: File bytes
            filename: Original filename

        Returns:
            (success: bool, url_or_error: str)
        """
        try:
            # Validate extension
            file_ext = Path(filename).suffix.lower()
            if file_ext not in StorageService.ALLOWED_EXTENSIONS:
                return False, f"Tipo de archivo no permitido. Usa: {', '.join(StorageService.ALLOWED_EXTENSIONS)}"

            # Validate size
            if len(file_data) > StorageService.MAX_FILE_SIZE:
                return (
                    False,
                    f"Archivo muy grande. Máximo {StorageService.MAX_FILE_SIZE // 1024 // 1024}MB",
                )

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid4())[:8]
            new_filename = f"{timestamp}_{unique_id}{file_ext}"

            # Create file path
            file_path = COMPROBANTES_DIR / new_filename

            # Save file
            with open(file_path, "wb") as f:
                f.write(file_data)

            log.info(f"File uploaded successfully: {new_filename}")

            # Return relative URL (for serving via /uploads/comprobantes/...)
            url = f"/uploads/comprobantes/{new_filename}"
            return True, url

        except Exception as e:
            log.error(f"Error uploading file: {e}")
            return False, f"Error al guardar archivo: {str(e)}"

    @staticmethod
    def get_file_path(filename: str) -> Path | None:
        """
        Get full file path for a filename.

        Args:
            filename: Filename to retrieve

        Returns:
            Path object if file exists, None otherwise
        """
        file_path = COMPROBANTES_DIR / filename

        # Security: ensure file is within COMPROBANTES_DIR
        if not file_path.resolve().is_relative_to(COMPROBANTES_DIR.resolve()):
            log.warning(f"Attempted path traversal: {filename}")
            return None

        if file_path.exists():
            return file_path

        return None

    @staticmethod
    def delete_file(filename: str) -> tuple[bool, str]:
        """
        Delete a file.

        Args:
            filename: Filename to delete

        Returns:
            (success: bool, message: str)
        """
        try:
            file_path = StorageService.get_file_path(filename)

            if not file_path:
                return False, "Archivo no encontrado"

            file_path.unlink()
            log.info(f"File deleted: {filename}")
            return True, "Archivo eliminado"

        except Exception as e:
            log.error(f"Error deleting file: {e}")
            return False, f"Error al eliminar: {str(e)}"
