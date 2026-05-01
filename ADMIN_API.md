# Panel de Gestión de Tenants - Documentación de API

**Versión**: 1.0.0
**Fecha**: 2026-04-30
**Autor**: JADS Studio

---

## 📋 Introducción

El Panel de Gestión de Tenants es una interfaz completa que permite a los superadmins monitorear y gestionar todos los operadores (tenants) de la plataforma JADSlink.

**Requisitos**: Solo usuarios con rol `superadmin` pueden acceder a estos endpoints.

---

## 🔑 Autenticación

Todos los endpoints requieren un token JWT válido en el header `Authorization`:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.jadslink.io/api/v1/admin/overview
```

**Response si no autorizado (403)**:
```json
{
  "detail": "Not authenticated"
}
```

---

## 📊 Endpoints

### 1. GET `/admin/overview`

**Descripción**: Obtiene estadísticas globales de toda la plataforma.

**Parámetros**: Ninguno

**Response (200)**:
```json
{
  "total_tenants": 45,
  "active_tenants": 42,
  "inactive_tenants": 3,

  "total_nodes": 128,
  "online_nodes": 112,
  "offline_nodes": 15,
  "degraded_nodes": 1,

  "total_tickets": 5430,
  "pending_tickets": 120,
  "active_tickets": 980,
  "expired_tickets": 4200,
  "revoked_tickets": 130,

  "active_sessions": 45,
  "total_revenue_estimate": 2450.00,

  "tenants_by_plan": [
    { "plan": "free", "count": 10 },
    { "plan": "basic", "count": 20 },
    { "plan": "standard", "count": 12 },
    { "plan": "pro", "count": 3 }
  ],

  "nodes_by_status": [
    { "status": "online", "count": 112 },
    { "status": "offline", "count": 15 },
    { "status": "degraded", "count": 1 }
  ]
}
```

**Caché**: 30 segundos (React Query)

---

### 2. GET `/admin/tenants`

**Descripción**: Lista todos los tenants con información detallada.

**Parámetros**: Ninguno

**Response (200)**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Transportes ABC",
    "slug": "transportes-abc",
    "plan_tier": "pro",
    "subscription_status": "active",
    "is_active": true,
    "created_at": "2026-03-15T10:30:00Z",
    "updated_at": "2026-04-20T14:45:30Z",
    "nodes_count": 5,
    "tickets_count": 234,
    "sessions_count": 8,
    "users_count": 3
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Turismo Caribeño",
    "slug": "turismo-caribeno",
    "plan_tier": "standard",
    "subscription_status": "active",
    "is_active": true,
    "created_at": "2026-02-10T09:15:00Z",
    "updated_at": "2026-04-25T11:20:15Z",
    "nodes_count": 3,
    "tickets_count": 156,
    "sessions_count": 4,
    "users_count": 2
  }
]
```

**Caché**: 60 segundos (React Query)

---

### 3. GET `/admin/tenants/{tenant_id}/stats`

**Descripción**: Obtiene estadísticas detalladas de un tenant específico.

**Parámetros**:
- `tenant_id` (path, UUID): ID del tenant

**Response (200)**:
```json
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_name": "Transportes ABC",
  "tenant_slug": "transportes-abc",
  "plan_tier": "pro",
  "is_active": true,
  "subscription_status": "active",

  "nodes_total": 5,
  "nodes_online": 4,
  "nodes_offline": 1,
  "nodes_degraded": 0,

  "tickets_total": 234,
  "tickets_pending": 12,
  "tickets_active": 45,
  "tickets_expired": 170,
  "tickets_revoked": 7,

  "sessions_active": 8,
  "revenue_estimate": 225.00
}
```

**Errores**:
- `404`: Tenant no encontrado

**Caché**: 30 segundos

---

### 4. GET `/admin/tenants/{tenant_id}/nodes`

**Descripción**: Lista todos los nodos de un tenant.

**Parámetros**:
- `tenant_id` (path, UUID): ID del tenant

**Response (200)**:
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "Bus 101 - Caracas",
    "serial": "SN-ABC-001",
    "status": "online",
    "last_seen_at": "2026-04-30T14:32:10Z",
    "location": {
      "lat": 10.4806,
      "lng": -66.9036,
      "address": "Avenida Bolívar, Caracas",
      "description": "Ruta Caracas-Maracay"
    },
    "wan_ip": "201.234.100.45"
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "name": "Bus 102 - Maracay",
    "serial": "SN-ABC-002",
    "status": "offline",
    "last_seen_at": "2026-04-30T11:15:30Z",
    "location": null,
    "wan_ip": null
  }
]
```

**Errores**:
- `404`: Tenant no encontrado

---

### 5. GET `/admin/tenants/{tenant_id}/tickets`

**Descripción**: Lista tickets de un tenant con paginación (100 por página).

**Parámetros**:
- `tenant_id` (path, UUID): ID del tenant
- `skip` (query, int): Offset para paginación (default: 0)
- `limit` (query, int): Cantidad por página (default: 100, máx: 500)

**Response (200)**:
```json
{
  "tickets": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "code": "A3K9P2X7",
      "status": "active",
      "created_at": "2026-04-30T10:00:00Z",
      "activated_at": "2026-04-30T10:05:30Z",
      "expires_at": "2026-04-30T10:35:00Z",
      "plan_name": "30 Minutos",
      "node_name": "Bus 101 - Caracas",
      "device_mac": "AA:BB:CC:DD:EE:FF"
    }
  ],
  "total": 234,
  "page": 1,
  "pages": 3
}
```

**Errores**:
- `404`: Tenant no encontrado

---

### 6. GET `/admin/tenants/{tenant_id}/sessions`

**Descripción**: Lista sesiones activas e históricas de un tenant.

**Parámetros**:
- `tenant_id` (path, UUID): ID del tenant
- `active_only` (query, bool): Filtrar solo sesiones activas (default: false)

**Response (200)**:
```json
[
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "ticket_id": "990e8400-e29b-41d4-a716-446655440004",
    "device_mac": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.1.100",
    "started_at": "2026-04-30T10:05:30Z",
    "expires_at": "2026-04-30T10:35:00Z",
    "is_active": true,
    "bytes_down": 15728640,
    "bytes_up": 2097152,
    "node_name": "Bus 101 - Caracas"
  }
]
```

**Errores**:
- `404`: Tenant no encontrado

---

### 7. PATCH `/admin/tenants/{tenant_id}/suspend`

**Descripción**: Suspende un tenant (is_active = false).

**Parámetros**:
- `tenant_id` (path, UUID): ID del tenant

**Response (200)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Transportes ABC",
  "slug": "transportes-abc",
  "is_active": false,
  "plan_tier": "pro",
  "subscription_status": "active",
  "created_at": "2026-03-15T10:30:00Z",
  "updated_at": "2026-04-30T15:00:00Z"
}
```

**Errores**:
- `404`: Tenant no encontrado
- `400`: Tenant ya está suspendido

---

### 8. PATCH `/admin/tenants/{tenant_id}/activate`

**Descripción**: Reactiva un tenant suspendido (is_active = true).

**Parámetros**:
- `tenant_id` (path, UUID): ID del tenant

**Response (200)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Transportes ABC",
  "slug": "transportes-abc",
  "is_active": true,
  "plan_tier": "pro",
  "subscription_status": "active",
  "created_at": "2026-03-15T10:30:00Z",
  "updated_at": "2026-04-30T15:05:00Z"
}
```

**Errores**:
- `404`: Tenant no encontrado
- `400`: Tenant ya está activo

---

## 📈 Casos de Uso

### Caso 1: Monitoreo Diario
1. Acceder a `/admin/overview` para ver estadísticas globales
2. Identificar tenants con nodos offline
3. Revisar tickets pendientes o expirados

### Caso 2: Soporte a un Operador Específico
1. Acceder a `/admin/tenants` para encontrar el operador
2. Hacer clic en el tenant para obtener `/admin/tenants/{id}/stats`
3. Ver nodos en `/admin/tenants/{id}/nodes` (ubicación, estado)
4. Revisar tickets recientes en `/admin/tenants/{id}/tickets`
5. Ver sesiones activas en `/admin/tenants/{id}/sessions`

### Caso 3: Mantenimiento de Cuenta
1. Suspender temporalmente un tenant con `/admin/tenants/{id}/suspend`
2. Realizar mantenimiento
3. Reactivar con `/admin/tenants/{id}/activate`

---

## 🔒 Seguridad

- ✅ Todos los endpoints requieren autenticación JWT
- ✅ Solo superadmins pueden acceder (validación con `get_superadmin()`)
- ✅ SQL injection imposible (ORM SQLAlchemy)
- ✅ XSS prevenido (respuestas JSON estructuradas)
- ✅ Rate limiting aplicable en el future

---

## 📊 Rendimiento

| Endpoint | Tiempo promedio | Caché |
|----------|-----------------|-------|
| `/overview` | 150ms | 30s |
| `/tenants` | 200ms | 60s |
| `/tenants/{id}/stats` | 100ms | 30s |
| `/tenants/{id}/nodes` | 80ms | 30s |
| `/tenants/{id}/tickets` | 200ms | 30s |
| `/tenants/{id}/sessions` | 150ms | 30s |

**Nota**: Los tiempos son estimaciones. React Query cachea todas las respuestas.

---

## 🧪 Testing

Los tests están en `api/tests/test_admin_tenants.py`.

**Ejecutar todos los tests de admin**:
```bash
pytest api/tests/test_admin_tenants.py -v
```

**Ejecutar un test específico**:
```bash
pytest api/tests/test_admin_tenants.py::TestAdminGlobalOverview::test_global_overview_success -v
```

**Cobertura de tests**: 13 tests, 100% de endpoints

---

## 🚀 Frontend

El componente React está en `dashboard/src/pages/AdminTenants.tsx`.

**Ruta de acceso**: `/admin/tenants`

**Características**:
- ✅ Selector dropdown de tenants
- ✅ 9 stat cards (4 globales + 5 por tenant)
- ✅ Sistema de 3 tabs (Nodos, Tickets, Sesiones)
- ✅ Paginación automática de tickets
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Dark mode integrado
- ✅ Skeleton loaders

---

## 🔄 Flujo de Datos

```
┌──────────────────────────────────────────────────┐
│ AdminTenants.tsx (React Component)               │
├──────────────────────────────────────────────────┤
│                                                  │
│  useQuery('admin/overview')          ──────────→ │ GET /admin/overview
│  useQuery('admin/tenants')           ──────────→ │ GET /admin/tenants
│  useQuery('admin/tenant-stats')      ──────────→ │ GET /admin/tenants/{id}/stats
│  useQuery('admin/tenant-nodes')      ──────────→ │ GET /admin/tenants/{id}/nodes
│  useQuery('admin/tenant-tickets')    ──────────→ │ GET /admin/tenants/{id}/tickets
│  useQuery('admin/tenant-sessions')   ──────────→ │ GET /admin/tenants/{id}/sessions
│                                                  │
└──────────────────────────────────────────────────┘
                       ↓
            Mostrar en Cards y Tabs
```

---

## 📝 Cambios Recientes

### v1.0.0 (2026-04-30)
- ✨ Implementación inicial del panel de gestión de tenants
- ✨ 8 nuevos endpoints en `/admin`
- ✨ Componente React completo con 600+ líneas
- ✨ 13 tests unitarios
- ✨ Documentación de API

---

## 🔗 Referencias

- [CLAUDE.md](./CLAUDE.md) - Arquitectura del proyecto
- [api/routers/admin.py](./api/routers/admin.py) - Implementación de endpoints
- [api/schemas/admin.py](./api/schemas/admin.py) - Schemas Pydantic
- [dashboard/src/pages/AdminTenants.tsx](./dashboard/src/pages/AdminTenants.tsx) - Componente React
- [dashboard/src/types/admin.ts](./dashboard/src/types/admin.ts) - Types TypeScript

---

## 📞 Soporte

Para reportar bugs o sugerir mejoras, crear un issue en:
https://github.com/adrpinto83/jadslink/issues

---

**Última actualización**: 2026-04-30
**Mantendor**: JADS Studio
