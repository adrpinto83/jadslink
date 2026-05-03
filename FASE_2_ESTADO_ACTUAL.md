# FASE 2: Estado Actual - 3 de Mayo, 2026

## Resumen Ejecutivo

Se ha implementado una nueva arquitectura **Nginx + FastAPI + PostgreSQL** separando completamente la responsabilidad del servicio de frontend del backend. El dashboard se sirve ahora como archivos estáticos a través de Nginx (puerto 3000), que a su vez proxy los requests a `/api/*` hacia el backend FastAPI (puerto 8000).

## Arquitectura Implementada

```
┌─────────────────────────────────────────────────────────┐
│                   Usuario Browser                        │
│              http://192.168.0.201:3000                   │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴──────────────┐
         │                          │
         ▼                          ▼
    [Archivos                   [API Proxy]
     Estáticos]                 [/api/v1/*]
         │                          │
         ▼                          ▼
┌────────────────────────────────────────────────────────┐
│              Nginx (Puerto 3000)                        │
│  ├─ try_files $uri /index.html (SPA routing)          │
│  ├─ Sirve dashboard/dist estático                      │
│  └─ Proxy /api/* → http://api:8000/api/               │
└────────────────────┬───────────────────────────────────┘
                     │
         ┌───────────┴──────────────┐
         │                          │
         ▼                          ▼
    [FastAPI]                  [PostgreSQL]
    Puerto 8000                 Puerto 5433
    - Routers                   - Tablas base
    - Middleware                - Datos de prueba
    - APScheduler               - Redis (6379)
```

## Componentes Implementados ✅

### 1. Docker Compose (`docker-compose.yml`)
- ✅ Servicio `dashboard` (nginx:alpine en puerto 3000)
- ✅ Servicio `api` (FastAPI en puerto 8000)
- ✅ Servicio `db` (PostgreSQL 15 en puerto 5433)
- ✅ Servicio `redis` (Redis 7 en puerto 6379)

### 2. Nginx (`nginx.conf`)
- ✅ Proxy inverso para `/api/` → `http://api:8000/api/`
- ✅ Proxy para `/health` → `http://api:8000/health`
- ✅ SPA routing: `try_files $uri $uri/ /index.html`
- ✅ Headers HTTP proxy (X-Real-IP, X-Forwarded-For, etc)

### 3. Frontend Dashboard
- ✅ Build compilado en `dashboard/dist`
- ✅ `.env.production` con `VITE_API_BASE_URL=/api/v1`
- ✅ URLs relativas para comunicación API a través del proxy

### 4. Backend API
- ✅ CORS actualizado para incluir `192.168.0.201:3000` y `192.168.0.201:8000`
- ✅ Endpoints `/health`, `/api/v1/*` funcionando
- ✅ Migraciones de base de datos (hasta revisión 0643195d1bb7)

### 5. Base de Datos
- ✅ Tablas creadas: tenants, users, plans, nodes, sessions, tickets, node_metrics
- ✅ Datos de prueba insertados:
  - Tenants: JADS Admin (enterprise), Demo Operator (starter)
  - Users: admin@jads.com (superadmin), operator@demo.com (operator)
  - Plans: 30 min ($2.50), 1 hora ($4.50), 1 día ($12.00)
  - Nodes: Bus 101 (SN-001-ABC, online)

## Tests de Funcionalidad ✅

| Prueba | URL | Estado | Resultado |
|--------|-----|--------|-----------|
| Dashboard carga | `http://localhost:3000` | ✅ | HTML de SPA se sirve |
| API health directo | `http://localhost:8000/health` | ✅ | JSON válido |
| Health vía proxy | `http://localhost:3000/health` | ✅ | JSON válido |
| API Docs | `http://localhost:8000/docs` | ✅ | Swagger UI funciona |
| Datos en BD | SQL query | ✅ | Tenants, Users, Plans creados |

## Problemas Identificados ⚠️

### 1. Login Endpoint Retorna 500
- **Request**: `POST /api/v1/auth/login` con `{"email": "operator@demo.com", "password": "123456"}`
- **Response**: `500 Internal Server Error`
- **Causa probable**:
  - Columnas de esquema mismatch (usuarios esperan otros campos)
  - Dependencia en campos que no existen en migraciones aplicadas
- **Necesario**: Debuggear error exacto en logs del API

### 2. Migraciones Divergentes en Alembic
- **Problema**: Dos ramas de migraciones (head):
  - `744fa42cca13` - add_free_subscription_fields_to_tenant
  - `a7c2f8d9e4b1` - create_pricing_plans_table
- **Impacto**: No se pudieron aplicar todas las migraciones
- **Solución**: Necesita merge de ramas o decidir cuál rama usar

### 3. Tipos PostgreSQL Duplicados
- **Error**: `type "paymentmethod" already exists`
- **Causa**: Migraciones intentan crear tipos que ya existen
- **Impacto**: Imposibilidad de aplicar todas las migraciones

## Pasos Siguientes (FASE 2 Continuación)

### Prioridad 1 - Autenticación Funcional
```
[ ] Debuggear error 500 en POST /api/v1/auth/login
[ ] Verificar que usuarios en BD cumplan con schema esperado
[ ] Probar login exitoso
[ ] Verificar tokens JWT generados correctamente
```

### Prioridad 2 - Dashboard Completamente Funcional
```
[ ] Confirmar que React Dashboard puede:
    [ ] Cargar página principal
    [ ] Llamar endpoints API desde JavaScript
    [ ] Mostrar datos de planes
    [ ] Mostrar datos de nodos
[ ] Testing de CORS desde navegador
```

### Prioridad 3 - Base de Datos Limpia
```
[ ] Resolver conflicto de migraciones
[ ] Aplicar todas las migraciones en orden correcto
  O
[ ] Justificar por qué paramos en 0643195d1bb7
```

### Prioridad 4 - Limpiar Ambiente
```
[ ] Eliminar directorios deprecated (openwrt-scripts, api/dashboard_static, etc)
[ ] Eliminar archivos .md redundantes
[ ] Consolidar documentación en un único archivo
```

## Credenciales de Prueba

```
Superadmin:
  Email: admin@jads.com
  Password: 123456
  Rol: superadmin

Operator:
  Email: operator@demo.com
  Password: 123456
  Rol: operator
```

## Acceso a Servicios

| Servicio | URL | Usuario | Pass |
|----------|-----|---------|------|
| Dashboard | `http://192.168.0.201:3000` | - | - |
| API Docs | `http://192.168.0.201:8000/docs` | - | - |
| API Health | `http://192.168.0.201:3000/health` | - | - |
| PostgreSQL | `localhost:5433` | jads | jadspass |
| Redis | `localhost:6379` | - | - |

## Commits Clave

- `c933441` - feat: nueva arquitectura con Nginx + API + BD limpia
- `15b4240` - feat: implementación local completamente funcional (base anterior)

## Notes para Próxima Sesión

1. **Enfoque**: Debuggear el error 500 del login es crítico para desbloquear todo lo demás
2. **Estrategia**: Si la columna de usuarios mismatch, considerar:
   - Migración manual para ajustar esquema
   - O resetear a commit anterior con migraciones working
3. **Arquitectura Confirmada**: Nginx + FastAPI está validado y funcionando bien
4. **Próximo Hito**: Dashboard mostrando datos en vivo (planes, nodos)
