# Solución: Error de Assets en Dashboard (Hostinger)

## Problema
```
Failed to load module script: Expected a JavaScript-or-Wasm module script but the server responded with a MIME type of "text/html". Strict MIME type checking is enforced for module scripts per HTML spec.
```

### Causa Raíz
El archivo compilado `dist/index.html` tenía rutas absolutas `/assets/` en lugar de relativas:
```html
<!-- ❌ Incorrecto -->
<script src="/assets/index-BD6wUIhk.js"></script>
<link href="/assets/index-CoJl_89v.css">
```

En Hostinger, cuando se accede a `/dashboard/`, estas rutas intentaban cargar desde `/assets/` (raíz del servidor) en lugar de `/dashboard/assets/`.

## Solución Implementada

### 1. Cambiar configuración de Vite
**Archivo**: `dashboard/vite.config.ts`
```typescript
// Antes: base: '/dashboard/'
// Después: base: './'
```

Con `base: './'`, las rutas generadas son relativas:
```html
<!-- ✅ Correcto -->
<script src="./assets/index-BD6wUIhk.js"></script>
<link href="./assets/index-CoJl_89v.css">
```

### 2. Script automático post-build
**Archivo**: `dashboard/fix-paths.js`

Corrección automática de rutas después de cada compilación (por si Vite genera rutas absolutas):
```javascript
html = html.replace(/src="\/assets\//g, 'src="./assets/');
html = html.replace(/href="\/assets\//g, 'href="./assets/');
```

### 3. Integración en build process
**Archivo**: `dashboard/package.json`
```json
"build": "tsc -b && vite build && node fix-paths.js"
```

### 4. Configuración Apache optimizada
**Archivo**: `dashboard/.htaccess`
```apache
# Rewrite rules para SPA (Single Page Application)
RewriteRule ^ index.html [QSA,L]

# MIME types correctos
AddType application/javascript .js
AddType text/css .css

# Cache headers
Header set Cache-Control "public, max-age=31536000, immutable"  # assets
Header set Cache-Control "public, max-age=0, must-revalidate"  # index.html
```

## Verificación

✅ **Rutas compiladas**:
```bash
$ cat dashboard/dist/index.html
<script src="./assets/index-BD6wUIhk.js"></script>
<link href="./assets/index-CoJl_89v.css">
```

✅ **Acceso a dashboard**:
```
https://wheat-pigeon-347024.hostingersite.com/dashboard/
```

✅ **Assets servidos correctamente**:
- `/dashboard/assets/index-BD6wUIhk.js` → JavaScript
- `/dashboard/assets/index-CoJl_89v.css` → CSS
- `/dashboard/favicon.svg` → SVG

## Cómo desplegar actualizaciones

```bash
# 1. Modificar código del dashboard
cd dashboard

# 2. Compilar (automáticamente corrige rutas)
npm run build

# 3. Subir a Hostinger
scp -P 65002 -r dist/* u938946830@217.65.147.159:/home/u938946830/domains/wheat-pigeon-347024.hostingersite.com/public_html/dashboard/

# O usar el script automatizado:
cd ..
./deploy_dashboard.sh
```

## Archivos modificados

```
dashboard/vite.config.ts       - base: './' en lugar de '/dashboard/'
dashboard/package.json         - Agregar fix-paths.js al build script
dashboard/fix-paths.js         - Nuevo: corrección automática de rutas
dashboard/.htaccess            - Nuevo: configuración Apache optimizada
dashboard/dist/index.html      - Rutas relativas ./assets/
```

## Notas técnicas

- **Rutas relativas vs absolutas**: Las rutas relativas (`./assets/`) funcionan desde cualquier subdirectorio, mientras que las absolutas (`/assets/`) siempre apuntan a la raíz del servidor.
- **SPA (Single Page Application)**: El `.htaccess` redirige todas las rutas desconocidas a `index.html` para que React Router maneje la navegación.
- **MIME types**: Apache debe servir `.js` como `application/javascript` (no `text/javascript` antiguo).
- **Cache headers**: Los assets con hash (versionados) tienen cache infinito, mientras que `index.html` no se cachea para permitir actualizaciones.

## Troubleshooting

| Error | Solución |
|-------|----------|
| 404 en rutas SPA | Verificar que `.htaccess` está en `/dashboard/` |
| "MIME type text/html" en JS | Verificar rutas relativas en `index.html` |
| Assets no encontrados | Verificar que `/dashboard/assets/` existe |
| Cache antiguo | Limpiar caché del navegador (Ctrl+Shift+Del) |

---

**Fecha**: 2026-04-28
**Versión**: 1.0 - Production Ready
