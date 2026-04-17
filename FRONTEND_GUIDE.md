# Guía Completa del Frontend - JADSlink Dashboard

## Estado Actual ✅

El frontend está **completamente funcional** y listo para uso. Todos los errores de TypeScript han sido corregidos y el build de producción se genera exitosamente.

---

## Configuración Inicial

### 1. Requisitos Previos

```bash
# Node.js 18+ y npm
node --version  # v18.0.0 o superior
npm --version   # 9.0.0 o superior
```

### 2. Instalación de Dependencias

```bash
cd /home/adrpinto/jadslink/dashboard
npm install
```

### 3. Configuración de Variables de Entorno

El archivo `.env` ya está configurado:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Nota**: Para producción, cambia esto a tu URL del servidor API real.

---

## Ejecutar en Modo Desarrollo

```bash
cd dashboard
npm run dev
```

El dashboard estará disponible en: **http://localhost:5173**

**Ventajas del modo dev**:
- Hot Module Replacement (HMR) - cambios en vivo
- Proxy automático a la API (configurado en `vite.config.ts`)
- Source maps para debugging

---

## Build de Producción

```bash
cd dashboard
npm run build
```

**Output**:
- Carpeta: `dashboard/dist/`
- Tamaño total: ~750 KB (minificado + gzipped: ~220 KB)
- Assets optimizados para producción

### Servir Build de Producción

```bash
# Opción 1: Usar vite preview
npm run preview

# Opción 2: Servir con cualquier servidor estático
npx serve dist

# Opción 3: Nginx, Apache, etc.
```

---

## Estructura del Proyecto

```
dashboard/
├── src/
│   ├── api/
│   │   └── client.ts          # Cliente Axios con interceptores JWT
│   ├── components/
│   │   ├── layout/
│   │   │   ├── DashboardLayout.tsx  # Layout principal
│   │   │   └── Sidebar.tsx          # Menú lateral
│   │   ├── ui/                      # Componentes shadcn/ui
│   │   ├── theme-provider.tsx       # Provider de tema (dark/light)
│   │   ├── theme-toggle.tsx         # Toggle de tema
│   │   └── NodeMap.tsx              # Mapa de nodos (Leaflet)
│   ├── pages/
│   │   ├── Login.tsx            # Página de login
│   │   ├── Register.tsx         # Registro de operadores
│   │   ├── Dashboard.tsx        # Overview
│   │   ├── Nodes.tsx            # Gestión de nodos
│   │   ├── NodeDetail.tsx       # Detalle de nodo
│   │   ├── Plans.tsx            # Gestión de planes
│   │   ├── Tickets.tsx          # Generación de tickets
│   │   ├── Sessions.tsx         # Sesiones activas
│   │   ├── Reports.tsx          # Reportes
│   │   ├── Billing.tsx          # Suscripciones Stripe
│   │   ├── Settings.tsx         # Configuración del tenant
│   │   └── Admin.tsx            # Panel superadmin
│   ├── stores/
│   │   └── auth.ts              # Zustand store para auth
│   ├── lib/
│   │   └── utils.ts             # Utilidades (cn, etc.)
│   ├── App.tsx                  # App principal
│   ├── Root.tsx                 # Root con redirección
│   ├── main.tsx                 # Entry point
│   ├── globals.css              # Estilos globales + Tailwind
│   ├── vite-env.d.ts            # Definiciones de tipos para Vite
│   └── global.d.ts              # Definiciones globales (CSS imports)
├── public/                      # Assets estáticos
├── .env                         # Variables de entorno
├── vite.config.ts               # Configuración de Vite
├── tailwind.config.ts           # Configuración de Tailwind
├── tsconfig.json                # Configuración de TypeScript
├── tsconfig.node.json           # TS config para archivos de Node
└── package.json
```

---

## Páginas y Funcionalidades

### 1. Login (`/login`)

**Funcionalidad**:
- Login con email y password
- Almacena tokens JWT en localStorage
- Redirección automática a `/dashboard`
- Manejo de errores de autenticación

**Credenciales de Prueba**:
```
Superadmin:
  Email: admin@jads.io
  Password: admin123

Operator (después de registro y aprobación):
  Email: tu-email@empresa.com
  Password: tu-password
```

### 2. Registro (`/register`)

**Funcionalidad**:
- Registro de nuevos operadores
- Validación de formulario
- Mensaje de éxito con instrucciones
- Estado pendiente (requiere aprobación de superadmin)

**Campos**:
- Nombre de la empresa
- Email
- Contraseña (mínimo 8 caracteres)
- Confirmar contraseña

### 3. Dashboard (`/dashboard`)

**Overview** con:
- Estadísticas principales (nodos, sesiones, tickets)
- Gráficas de uso
- Acceso rápido a funciones principales

### 4. Nodos (`/dashboard/nodes`)

**Funcionalidades**:
- **Mapa interactivo** con todos los nodos (Leaflet)
- **Tabla de nodos** con:
  - Nombre
  - Serial
  - Estado (online/offline/maintenance)
  - Última vez visto
- **CRUD completo**:
  - Crear nuevo nodo
  - Editar nodo existente
  - Ver detalle de nodo
  - Eliminar nodo (soft delete)

**Integración con Agent**:
- Campo `api_key` generado automáticamente
- Se muestra para copiar al agent
- Instrucciones de instalación

### 5. Planes (`/dashboard/plans`)

**Funcionalidades**:
- **Tabla de planes** con:
  - Nombre
  - Duración (30 min, 1 hr, 1 día, etc.)
  - Precio (USD)
  - Límites de ancho de banda
  - Estado (activo/inactivo)
- **CRUD completo**:
  - Crear plan
  - Editar plan
  - Eliminar plan (soft delete)
  - Activar/desactivar

**Validaciones**:
- Duración mínima: 1 minuto
- Precio mínimo: $0.01
- Bandwidth opcional

### 6. Tickets (`/dashboard/tickets`)

**Funcionalidades**:
- **Generación de tickets**:
  - Seleccionar nodo
  - Seleccionar plan
  - Cantidad (1-50)
- **Visualización**:
  - Código alfanumérico (8 caracteres)
  - QR code en base64
  - Logo del tenant (si está configurado)
- **Impresión**:
  - Botón print por ticket
  - PDF-ready con logo
- **Filtros**:
  - Por nodo
  - Por plan
  - Por estado (pending, active, expired)

### 7. Sesiones (`/dashboard/sessions`)

**Funcionalidades**:
- **Tabla de sesiones activas**:
  - Usuario (MAC/IP)
  - Nodo
  - Plan
  - Tiempo restante
  - Datos consumidos
- **Acciones**:
  - Desconectar sesión manualmente
  - Ver historial
- **Filtros**:
  - Por nodo
  - Por estado
  - Por fecha

### 8. Reportes (`/dashboard/reports`)

**Funcionalidades**:
- **Gráficas** (Recharts):
  - Ventas por período
  - Sesiones activas
  - Uso de ancho de banda
  - Top nodos
- **Filtros**:
  - Rango de fechas
  - Por nodo
- **Exportación**:
  - CSV
  - Excel
  - PDF (futuro)

### 9. Billing (`/dashboard/billing`)

**Funcionalidades**:
- **Estado de suscripción**:
  - Plan actual (starter, growth, enterprise)
  - Fecha de renovación
  - Límites (nodos, tickets)
  - Uso actual
- **Gestionar suscripción**:
  - Upgrade/downgrade
  - Método de pago (Stripe)
  - Historial de facturas
- **Portal de Stripe**:
  - Botón para abrir portal de cliente

### 10. Settings (`/dashboard/settings`)

**Funcionalidades**:
- **Información del tenant**:
  - Nombre
  - Slug
  - Plan
  - Estado
- **Personalización**:
  - Logo URL
  - Color primario (picker)
  - Dominio personalizado
- **Guardar cambios**:
  - Validación
  - Feedback de éxito/error

### 11. Admin (`/dashboard/admin`)

**Solo visible para superadmin**

**Funcionalidades**:
- **Gestión de tenants**:
  - Listar todos los operadores
  - Aprobar/rechazar registros
  - Suspender tenants
  - Ver métricas globales
- **Mapa global**:
  - Todos los nodos de todos los tenants
- **Estadísticas**:
  - Total de tenants
  - Total de nodos
  - Sesiones activas globales
  - Revenue total

---

## Temas (Dark/Light Mode)

El dashboard soporta **3 modos**:
- **Light**: Tema claro
- **Dark**: Tema oscuro
- **System**: Sigue la preferencia del sistema

**Cómo cambiar el tema**:
- Click en el botón de sol/luna en el sidebar
- Seleccionar modo deseado
- Preferencia se guarda en localStorage

**Personalización**:
- Los colores se definen en `globals.css`
- Variables CSS con prefijo `--`
- Soporte completo para modo oscuro con Tailwind

---

## API Client y Autenticación

### Interceptores

El archivo `src/api/client.ts` configura interceptores para:

**Request Interceptor**:
```typescript
// Agrega automáticamente el token JWT a todas las requests
Authorization: Bearer <access_token>
```

**Response Interceptor**:
```typescript
// Si recibe 401:
// 1. Intenta refresh token
// 2. Si refresh OK: reintenta request original
// 3. Si refresh falla: redirect a /login
```

### Manejo de Tokens

```typescript
// Tokens se almacenan en localStorage
localStorage.getItem('access_token')
localStorage.getItem('refresh_token')

// Refresh automático cada vez que access_token expira
```

### Logout

```typescript
// Limpia localStorage y redirect a login
useAuthStore.getState().logout()
```

---

## Componentes UI (shadcn/ui)

Todos los componentes están en `src/components/ui/`:

| Componente | Uso |
|------------|-----|
| `button.tsx` | Botones con variantes |
| `card.tsx` | Tarjetas de contenido |
| `table.tsx` | Tablas con datos |
| `input.tsx` | Inputs de formulario |
| `label.tsx` | Labels de formulario |
| `badge.tsx` | Badges de estado |
| `dropdown-menu.tsx` | Menús desplegables |

**Variantes disponibles**:
- Button: default, destructive, outline, secondary, ghost, link
- Badge: default, secondary, destructive, outline

---

## Correcciones Realizadas

### 1. TypeScript Config
- ✅ Agregado `ignoreDeprecations: "6.0"` en tsconfig.json
- ✅ Agregado `composite: true` en tsconfig.node.json
- ✅ Agregado `emitDeclarationOnly: true` para builds

### 2. Type Definitions
- ✅ Creado `vite-env.d.ts` para `import.meta.env`
- ✅ Creado `global.d.ts` para CSS imports
- ✅ Corregido imports de `next-themes`

### 3. Component Fixes
- ✅ `theme-provider.tsx` - removido import innecesario de React
- ✅ `theme-toggle.tsx` - removido import innecesario de React
- ✅ `dropdown-menu.tsx` - agregado imports de `VariantProps`, `Check`, `Circle`
- ✅ `Nodes.tsx` - corregido variant de Badge ("success" → "default")
- ✅ `Tickets.tsx` - corregido prop de `useReactToPrint` ("content" → "contentRef")

### 4. Build Issues
- ✅ Todos los errores de TypeScript resueltos
- ✅ Build de producción exitoso
- ✅ Bundle size optimizado (~220 KB gzipped)

---

## Troubleshooting

### Error: Cannot GET /

**Solución**: Asegúrate de que el servidor de desarrollo esté corriendo:
```bash
npm run dev
```

### Error: Network Error / CORS

**Solución**: Verifica que el backend esté corriendo:
```bash
docker compose ps
curl http://localhost:8000/api/v1/health
```

### Error: 401 Unauthorized

**Solución**: Token expirado o inválido. Cierra sesión y vuelve a iniciar:
```bash
localStorage.clear()  # En consola del navegador
```

### Error: Module not found

**Solución**: Reinstala dependencias:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Build falla con errores de TypeScript

**Solución**: Verifica que todos los archivos de configuración estén correctos:
```bash
# Verificar tsconfig.json
cat tsconfig.json | grep ignoreDeprecations

# Verificar que existan los archivos .d.ts
ls src/*.d.ts
```

---

## Testing del Frontend

### Test Manual Rápido

1. **Login**:
   ```bash
   # Abrir http://localhost:5173/login
   # Login con: admin@jads.io / admin123
   ```

2. **Crear un Plan**:
   ```bash
   # Ir a /dashboard/plans
   # Click "Nuevo Plan"
   # Llenar formulario y guardar
   ```

3. **Crear un Nodo**:
   ```bash
   # Ir a /dashboard/nodes
   # Click "Nuevo Nodo"
   # Llenar datos y guardar
   # Copiar el API_KEY generado
   ```

4. **Generar Tickets**:
   ```bash
   # Ir a /dashboard/tickets
   # Seleccionar nodo y plan
   # Cantidad: 5
   # Click "Generar"
   # Verificar QR codes
   ```

5. **Ver Mapa**:
   ```bash
   # Ir a /dashboard/nodes
   # Verificar que el mapa muestre el nodo
   # Hacer click en el marcador
   ```

6. **Cambiar Tema**:
   ```bash
   # Click en botón sol/luna en sidebar
   # Seleccionar Light/Dark/System
   # Verificar que cambie el tema
   ```

---

## Configuración para Producción

### 1. Variables de Entorno

Crear `.env.production`:
```env
VITE_API_BASE_URL=https://api.tudominio.com/api/v1
```

### 2. Build

```bash
npm run build
```

### 3. Deploy

**Opción A: Servir con el backend (FastAPI)**
```bash
# Copiar build al backend
cp -r dist/* ../api/static/

# FastAPI servirá automáticamente desde /static
```

**Opción B: CDN (Vercel, Netlify, etc.)**
```bash
# Deploy dist/ folder to CDN
# Configure rewrites for SPA:
#   /* -> /index.html
```

**Opción C: Nginx**
```nginx
server {
    listen 80;
    server_name tudominio.com;
    root /var/www/jadslink/dist;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

---

## Próximas Mejoras

- [ ] Tests E2E con Playwright/Cypress
- [ ] Code splitting para reducir bundle inicial
- [ ] PWA support (offline mode)
- [ ] WebSocket para updates en tiempo real
- [ ] Optimización de imágenes
- [ ] i18n (internacionalización)

---

## Contacto y Soporte

**Proyecto**: JADS Studio — Venezuela
**GitHub**: [github.com/adrpinto83/jadslink](https://github.com/adrpinto83/jadslink)
**Documentación**: Ver `/docs` en el repositorio

---

**Última actualización**: 2026-04-17
**Versión del Dashboard**: 1.0.0
**Estado**: ✅ Producción Ready
