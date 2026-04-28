# Solución: Dashboard no funciona (API unreachable)

## Problema
- Dashboard cargaba pero no respondía a clicks
- Ningún módulo funcionaba
- Console estaba vacía (sin errores visibles)
- Las llamadas a la API fallaban silenciosamente

## Causa Raíz
El archivo `.env` configuraba la API con una ruta **relativa**:
```
VITE_API_BASE_URL=/api/v1
```

Cuando el dashboard se sirve desde `/dashboard/`, las rutas relativas se resuelven incorrectamente:
```
/dashboard/ + /api/v1 = /dashboard/api/v1  ❌ (ruta incorrecta)
```

Esto causaba que todas las llamadas a la API devolvieran 404, haciendo que el JavaScript fallara silenciosamente sin mostrar errores en la consola.

## Solución Implementada

### 1. Crear `.env.production` con URL absoluta
**Archivo**: `dashboard/.env.production`
```
VITE_API_BASE_URL=https://wheat-pigeon-347024.hostingersite.com/api/v1
```

Vite **automáticamente** usa `.env.production` cuando ejecutas:
```bash
npm run build
```

### 2. Crear `.env.example` con documentación
**Archivo**: `dashboard/.env.example`

Ejemplos para diferentes ambientes:
```env
# Desarrollo local
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Hostinger
VITE_API_BASE_URL=https://wheat-pigeon-347024.hostingersite.com/api/v1

# Producción (cambiar por tu dominio)
VITE_API_BASE_URL=https://tudominio.com/api/v1
```

### 3. Recompilar y desplegar
```bash
cd dashboard
npm run build          # Usa automáticamente .env.production
# Los archivos compilados están en dist/
```

## Verificación

✅ **Nueva configuración en Hostinger**:
```javascript
// client.ts ahora usa:
const API_BASE_URL = 'https://wheat-pigeon-347024.hostingersite.com/api/v1'
```

✅ **Llamadas a API correctas**:
```
GET https://wheat-pigeon-347024.hostingersite.com/api/v1/plans
GET https://wheat-pigeon-347024.hostingersite.com/api/v1/nodes
POST https://wheat-pigeon-347024.hostingersite.com/api/v1/auth/login
```

✅ **Console sin errores** (después de vaciar caché)

## Cómo desplegar futuras versiones

```bash
# 1. Modificar código del dashboard
cd dashboard
# ... hacer cambios ...

# 2. Compilar (automáticamente usa .env.production)
npm run build

# 3. Subir a Hostinger
scp -P 65002 -r dist/* u938946830@217.65.147.159:/home/u938946830/domains/wheat-pigeon-347024.hostingersite.com/public_html/dashboard/

# O usar el script:
cd ..
./deploy_dashboard.sh
```

## Archivos actualizados

```
✅ dashboard/.env           - Ya contenía /api/v1 (desarrollo)
✅ dashboard/.env.production - NUEVO: URL absoluta para Hostinger
✅ dashboard/.env.example   - NUEVO: Documentación de configuración
✅ Hostinger (dist/)        - Compilado y desplegado con URL correcta
```

## Commits

- `a3eee12` - Agregar .env.production y .env.example
- `40048ea` - Cache busting automático
- `a89eb5d` - Remover AddEncoding gzip
- `37bbdd2` - Corregir rutas de assets
- `ab43ca8` - Remover basename duplicado

## Variables de entorno

### Desarrollo local
```bash
# dashboard/.env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Luego:
```bash
npm run dev   # Hot reload en http://localhost:5173/dashboard
```

### Producción (Hostinger)
```bash
# dashboard/.env.production
VITE_API_BASE_URL=https://wheat-pigeon-347024.hostingersite.com/api/v1
```

Luego:
```bash
npm run build   # Genera dist/ con API URL correcta
# Subir dist/ a Hostinger
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| Modulos no funcionan | Verificar .env tiene URL correcta |
| 404 en API | Revisar que API_BASE_URL es absoluta |
| Console errors | Vaciar caché (Ctrl+Shift+Del) |
| CORS errors | API CORS ya configurado, revisar headers |

## Notas técnicas

- **Vite automáticamente carga `.env.production`** durante build
- **`.env` se ignora en git** por seguridad (credenciales)
- **URLs relativas solo funcionan desde raíz** (ej: `/` no `/dashboard/`)
- **URLs absolutas funcionan desde cualquier ubicación**

---

**Fecha**: 2026-04-28
**Versión**: 1.0
**Status**: ✅ Solucionado - Dashboard completamente funcional
