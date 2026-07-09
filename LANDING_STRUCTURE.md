# Estructura de la Landing Page - JADSLink

## Ubicación en Producción

**URL**: https://link.jadsstudio.com/
**Directorio**: `~/domains/jadsstudio.com/public_html/link/`

## Estructura de Archivos

```
link/
├── index.html          # Landing page promocional (58KB, 1110 líneas)
├── app.php             # Proxy PHP para FastAPI/uvicorn (panel administrativo)
├── .htaccess           # Configuración de rutas
└── static/
    ├── css/
    │   └── app.css     # Estilos de la landing y dashboard
    └── js/
        └── app.js      # JavaScript de la landing y dashboard
```

## Configuración de Rutas (.htaccess)

```apache
PassengerEnabled Off
DirectoryIndex index.html

RewriteEngine On

# Ruta del panel administrativo (proxy a FastAPI)
RewriteRule ^app$ app.php [L]
RewriteRule ^app/(.*)$ app.php [L]

# API requests van al proxy
RewriteCond %{REQUEST_URI} ^/api/
RewriteRule ^(.*)$ app.php [L,QSA]

# Static files se sirven directamente
RewriteCond %{REQUEST_FILENAME} -f
RewriteRule ^ - [L]
```

## URLs y Funcionalidad

| URL | Archivo | Descripción |
|-----|---------|-------------|
| `https://link.jadsstudio.com/` | `index.html` | Landing page promocional de JADSLink |
| `https://link.jadsstudio.com/app` | `app.php` → FastAPI | Panel administrativo (login/dashboard) |
| `https://link.jadsstudio.com/api/*` | `app.php` → FastAPI | API endpoints |
| `https://link.jadsstudio.com/static/*` | Archivos estáticos | CSS, JS, imágenes |

## Contenido de la Landing Page

### Secciones

1. **Header**
   - Logo JADSLink (SVG inline)
   - Botón "Iniciar sesión" → Cambia a pantalla de login

2. **Hero**
   - Título: "Vende Internet Donde Quieras"
   - Subtítulo explicativo
   - CTAs: "Comenzar ahora" y "Ya tengo cuenta"
   - Stats: Setup 5min, 0 infraestructura, 24/7 acceso

3. **Casos de Uso**
   - Camping & Zonas Remotas (con imagen de Unsplash)
   - Eventos & Festivales
   - Transporte de Larga Distancia
   - Playas & Turismo

4. **Cómo Funciona** (4 pasos)
   - Instalar punto de acceso
   - Configurar planes y precios
   - Los usuarios compran acceso
   - Recibir pagos automáticamente

5. **JADSLink en Acción** (Galería de imágenes)
   - Antena satelital en zona remota
   - Router portátil
   - Personas usando internet

6. **Beneficios** (6 items)
   - Sin infraestructura fija
   - Configura en minutos
   - Monetización automática
   - Panel de control completo
   - Seguro y estable
   - Multi-plataforma

7. **CTA Final**
   - "¿Listo para empezar?"
   - Botón: "Crear cuenta gratis"
   - Nota: "14 días de prueba · Sin tarjeta de crédito"

8. **Footer**
   - Logo JADSLink
   - Links: Iniciar sesión, Crear cuenta
   - Copyright: "© 2026 JADSLink · Desarrollado por JADS Studio"

### Pantallas Integradas

El `index.html` contiene múltiples "screens" que se intercambian con JavaScript:

- `#landing-screen` - Landing promocional (mostrada por defecto)
- `#login-screen` - Login y signup
- `#dashboard-screen` - Dashboard completo (se carga tras login exitoso)

## Flujo de Usuario

1. Usuario entra a `https://link.jadsstudio.com/`
2. Ve la landing page promocional
3. Click en "Iniciar sesión" o "Comenzar ahora"
4. Aparece formulario de login/signup (sin cambiar de página)
5. Tras login exitoso, se muestra el dashboard (cargado desde `/api`)
6. El dashboard interactúa con la API FastAPI via `app.php` (proxy)

## Sincronización

### Local → GitHub → Hostinger

```bash
# 1. Actualizar landing en local
cd /home/adrpinto/jadslink/landing
# Editar index.html o static/*

# 2. Commit y push
git add landing/
git commit -m "feat(landing): actualizar contenido de landing page"
git push origin feature/vendor-jadslink-app-and-pg-migration

# 3. Deploy a Hostinger
cd ~/jadslink-app
git pull origin feature/vendor-jadslink-app-and-pg-migration
cp landing/index.html ~/domains/jadsstudio.com/public_html/link/
cp -r landing/static/* ~/domains/jadsstudio.com/public_html/link/static/
```

### Hostinger → Local (backup)

```bash
# Desde local
scp -P 65002 u938946830@217.65.147.159:~/domains/jadsstudio.com/public_html/link/index.html ~/jadslink/landing/
scp -r -P 65002 u938946830@217.65.147.159:~/domains/jadsstudio.com/public_html/link/static ~/jadslink/landing/
```

## Notas Importantes

1. **NO sobrescribir `index.html` con el proxy PHP**
   - La landing page DEBE ser `index.html`
   - El proxy PHP está en `app.php`

2. **CSS y JS compartidos**
   - Los archivos en `/static` son usados tanto por la landing como por el dashboard
   - Actualizar con cuidado para no romper ninguno de los dos

3. **Versión del CSS/JS**
   - El `index.html` incluye `?v=1783250272` en los links de CSS/JS
   - Actualizar este timestamp cuando se modifiquen los archivos para forzar recarga

4. **Imágenes de Unsplash**
   - La landing usa imágenes de Unsplash vía URL directa
   - Considerar descargarlas localmente para mejor rendimiento

---

**Última actualización**: 2026-07-05
**Restaurada desde**: `~/jadslink-hostinger/frontend/index.html`
**Estado**: ✅ Operativa en producción
