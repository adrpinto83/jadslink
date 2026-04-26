"""File handling utilities for uploads like logos."""

import os
import uuid
from pathlib import Path
from fastapi import UploadFile
import aiofiles


UPLOAD_DIR = Path("uploads/logos")


async def save_logo_file(file: UploadFile, contents: bytes) -> str:
    """
    Save a logo file and return its relative URL path.

    Args:
        file: The uploaded file
        contents: The file contents (already read)

    Returns:
        The relative path to access the file (e.g., "/uploads/logos/uuid.jpg")
    """
    # Create uploads directory if it doesn't exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    # Return relative URL path
    return f"/uploads/logos/{unique_filename}"


def cleanup_logo_file(file_path: str) -> None:
    """
    Delete a logo file if it exists.

    Args:
        file_path: The relative path to the file (e.g., "/uploads/logos/uuid.jpg")
    """
    if not file_path:
        return

    # Remove leading slash for file system path
    full_path = Path(file_path.lstrip("/"))

    try:
        if full_path.exists():
            full_path.unlink()
    except Exception:
        # Log error but don't fail if file deletion fails
        pass
