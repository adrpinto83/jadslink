# FASE 2: Upload de Comprobantes - Almacenamiento Local

**Fecha**: 27 de Abril de 2026
**Status**: 🔲 PENDIENTE
**Modificación**: Usar almacenamiento local en lugar de Cloudflare R2

## Resumen

En lugar de usar Cloudflare R2, vamos a almacenar los comprobantes en el sistema local del servidor.

### Estrategia de Almacenamiento Local

```
/home/adrpinto/jadslink/api/uploads/
├── comprobantes/
│   ├── [tenant_id]/
│   │   ├── [upgrade_id]_comprobante.jpg
│   │   ├── [upgrade_id]_comprobante.png
│   │   └── [upgrade_id]_comprobante.pdf
│   └── ...
└── metadata.json (índice de archivos)
```

## Archivos a Crear

### 1. `api/services/local_storage_service.py`

Servicio para manejar upload/descarga de archivos locales:

```python
from pathlib import Path
from decimal import Decimal
from uuid import UUID
from PIL import Image
import io
import os

class LocalStorageService:
    BASE_DIR = Path(__file__).parent.parent / "uploads" / "comprobantes"
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_TYPES = {'image/png', 'image/jpeg', 'application/pdf'}

    @classmethod
    def ensure_dir(cls, tenant_id: UUID):
        """Crear directorio para tenant si no existe"""
        tenant_dir = cls.BASE_DIR / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir

    @classmethod
    async def upload_comprobante(
        cls, 
        file_data: bytes, 
        filename: str, 
        tenant_id: UUID, 
        upgrade_id: UUID
    ) -> str:
        """
        Subir comprobante y retornar ruta relativa.
        - Comprime imágenes (max 1200x1200, quality 85)
        - Valida tipos de archivo
        - Retorna: uploads/comprobantes/[tenant_id]/[upgrade_id]_comprobante.jpg
        """
        # Validar tipo y tamaño
        if len(file_data) > cls.MAX_FILE_SIZE:
            raise ValueError("Archivo muy grande (max 5MB)")

        # Obtener extensión
        ext = Path(filename).suffix.lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.pdf']:
            raise ValueError("Tipo de archivo no permitido")

        # Compresión para imágenes
        if ext in ['.png', '.jpg', '.jpeg']:
            try:
                img = Image.open(io.BytesIO(file_data))
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                file_data = buffer.getvalue()
                ext = '.jpg'
            except Exception as e:
                log.warning(f"Error compressing image: {e}, using original")

        # Generar nombre único
        safe_filename = f"{upgrade_id}_comprobante{ext}"
        
        # Crear directorio del tenant
        tenant_dir = cls.ensure_dir(tenant_id)
        file_path = tenant_dir / safe_filename
        
        # Guardar archivo
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Retornar ruta relativa
        relative_path = f"uploads/comprobantes/{tenant_id}/{safe_filename}"
        return relative_path

    @classmethod
    async def get_comprobante_url(cls, tenant_id: UUID, upgrade_id: UUID) -> str | None:
        """Obtener URL del comprobante si existe"""
        tenant_dir = cls.BASE_DIR / str(tenant_id)
        
        # Buscar archivos con el patrón [upgrade_id]_comprobante.*
        for ext in ['.jpg', '.png', '.pdf']:
            file_path = tenant_dir / f"{upgrade_id}_comprobante{ext}"
            if file_path.exists():
                return f"uploads/comprobantes/{tenant_id}/{upgrade_id}_comprobante{ext}"
        
        return None

    @classmethod
    async def delete_comprobante(cls, tenant_id: UUID, upgrade_id: UUID) -> bool:
        """Eliminar comprobante"""
        tenant_dir = cls.BASE_DIR / str(tenant_id)
        
        for ext in ['.jpg', '.png', '.pdf']:
            file_path = tenant_dir / f"{upgrade_id}_comprobante{ext}"
            if file_path.exists():
                file_path.unlink()
                return True
        
        return False
```

### 2. `api/routers/uploads.py` (NUEVO)

Endpoint para upload de comprobantes:

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_tenant
from models.tenant import Tenant
from services.local_storage_service import LocalStorageService

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])

@router.post("/comprobante")
async def upload_comprobante(
    file: UploadFile = File(...),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Upload de comprobante de pago.
    
    Formatos aceptados: PNG, JPG, PDF
    Tamaño máximo: 5MB
    
    Retorna: {"url": "uploads/comprobantes/[tenant_id]/[filename]"}
    """
    if not current_tenant:
        raise HTTPException(status_code=403, detail="No tenant found")

    # Validar tipo MIME
    if file.content_type not in ['image/png', 'image/jpeg', 'application/pdf']:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo no permitido: {file.content_type}. Usa PNG, JPG o PDF."
        )

    # Leer contenido
    contents = await file.read()

    # Validar tamaño (5MB)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Archivo muy grande (max 5MB)")

    try:
        # Subir archivo
        url = await LocalStorageService.upload_comprobante(
            file_data=contents,
            filename=file.filename,
            tenant_id=current_tenant.id,
            upgrade_id=None  # Se usa para buscar luego
        )
        
        return {
            "url": url,
            "filename": file.filename,
            "size": len(contents),
            "type": file.content_type
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Error al subir archivo")


@router.get("/comprobante/{upgrade_id}")
async def get_comprobante(
    upgrade_id: str,
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """Obtener URL del comprobante de una solicitud"""
    from uuid import UUID
    
    try:
        upgrade_uuid = UUID(upgrade_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")

    url = await LocalStorageService.get_comprobante_url(current_tenant.id, upgrade_uuid)
    
    if not url:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    
    return {"url": url}
```

### 3. Servir archivos estáticos en FastAPI

En `api/main.py`, agregar:

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Montar directorio de uploads como estático
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
```

## Archivos a Modificar

### `api/main.py`

Agregar mount de directorio estático para servir uploads:

```python
# Alrededor de línea 150-160, después de crear la app:
app.mount("/uploads", StaticFiles(directory="api/uploads"), name="uploads")
```

### `dashboard/src/components/PagoMovilForm.tsx`

Crear componente `FileUpload`:

```typescript
import { useState } from 'react';
import { api } from '@/api/client';
import { toast } from 'sonner';

interface FileUploadProps {
  onUploadComplete: (url: string) => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Preview
    setPreview(URL.createObjectURL(file));

    // Upload
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/uploads/comprobante', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onUploadComplete(response.data.url);
      toast.success('Comprobante subido correctamente');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error al subir archivo');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium">
        Comprobante de Pago
        <span className="text-red-500">*</span>
      </label>
      
      <input
        type="file"
        accept=".png,.jpg,.jpeg,.pdf"
        onChange={handleFileChange}
        disabled={uploading}
        className="block w-full text-sm border rounded-lg p-2"
      />
      
      {preview && preview.endsWith('.pdf') === false && (
        <img src={preview} alt="Preview" className="max-h-40 rounded-lg" />
      )}
      
      {uploading && <p className="text-sm text-gray-500">Subiendo...</p>}
    </div>
  );
}
```

Integrarlo en `PagoMovilForm.tsx`:

```typescript
import { FileUpload } from './FileUpload';

// En el formulario:
<FileUpload 
  onUploadComplete={(url) => {
    setFormData({...formData, comprobante_url: url});
    toast.success('Comprobante listo para enviar');
  }}
/>
```

## Estructura de Directorios

```
/home/adrpinto/jadslink/
├── api/
│   ├── uploads/
│   │   ├── comprobantes/
│   │   │   ├── [tenant_id_1]/
│   │   │   │   ├── [upgrade_id_1]_comprobante.jpg
│   │   │   │   ├── [upgrade_id_2]_comprobante.pdf
│   │   │   │   └── ...
│   │   │   ├── [tenant_id_2]/
│   │   │   └── ...
│   │   └── .gitkeep
│   ├── services/
│   │   └── local_storage_service.py (NUEVO)
│   └── routers/
│       └── uploads.py (NUEVO)
└── ...
```

## Ventajas del Almacenamiento Local

✅ **No hay costos externos** (sin R2)
✅ **Control total** de archivos
✅ **Rápido** (sin latencia de red)
✅ **Seguro** (archivos privados en servidor)
✅ **Fácil de debuggear**

## Desventajas / Consideraciones

⚠️ **Espacio en disco** - Necesita monitoreo
⚠️ **Backups** - Incluir carpeta uploads en backups
⚠️ **Escalado** - Con miles de comprobantes, considerar archivos externos después

## Workflow Completo

### 1. Usuario sube comprobante
```
POST /api/v1/uploads/comprobante
→ FormData con archivo
→ Servicio comprime/valida
→ Guarda en api/uploads/comprobantes/[tenant_id]/
→ Retorna URL relativa
```

### 2. Frontend obtiene URL
```typescript
{
  "url": "uploads/comprobantes/55ddb132-dcea-4a9d/c6edb0a4-a7ab_comprobante.jpg",
  "filename": "IMG_20260427.jpg",
  "size": 125000,
  "type": "image/jpeg"
}
```

### 3. Incluir en solicitud de upgrade
```json
{
  "upgrade_type": "extra_tickets",
  "ticket_quantity": 50,
  "payment_method": "mobile_pay",
  "payment_details": {
    "banco_origen": "Bancamiga",
    "cédula_pagador": "V-12345678",
    "referencia_pago": "1234567890",
    "comprobante_url": "uploads/comprobantes/55ddb132-dcea-4a9d/c6edb0a4-a7ab_comprobante.jpg"
  }
}
```

### 4. Admin puede descargar/ver comprobante
```
GET /uploads/comprobantes/[tenant_id]/[upgrade_id]_comprobante.jpg
→ Imagen/PDF en navegador o descarga
```

## Consideraciones de Seguridad

⚠️ **Ruta traversal** - Validar nombres de archivo (ya lo hace el servicio)
⚠️ **Extensión de archivo** - Validar MIME type + extensión
⚠️ **Virus** - Considerar escaneo con ClamAV en producción
⚠️ **Permisos** - Los archivos son privados al tenant (no públicos)

## Próximos Pasos

1. Crear `local_storage_service.py`
2. Crear `routers/uploads.py`
3. Montar directorio en FastAPI
4. Crear componente `FileUpload` en frontend
5. Testing de upload y validación
6. .gitignore para `/api/uploads/*` (excepto .gitkeep)

---

**Siguiente**: FASE 3 - Emails automáticos con Resend (ya implementada ✅)
