# JADSlink — Arquitectura Completa y Roadmap

**Proyecto**: Plataforma SaaS Multi-tenant de Conectividad Satelital Comercial
**Organización**: JADS Studio — Venezuela
**Principio Rector**: **Liviano Primero** — Cada dependencia debe justificarse por bajo consumo de RAM/CPU
**Estado**: FASE 1-5 ✅ Completadas | FASE 6-10 🔄 Planificadas
**Última Actualización**: Mayo 2026 | **Versión**: 2.0.0

---

## 📋 Índice

1. [Visión y Modelo de Negocio](#1-visión-y-modelo-de-negocio)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Técnico](#3-stack-técnico)
4. [Modelos de Datos](#4-modelos-de-datos)
5. [API Endpoints](#5-api-endpoints)
6. [Estado Actual (Mayo 2026)](#6-estado-actual-mayo-2026)
7. [Fases de Desarrollo](#7-fases-de-desarrollo)
8. [Deployment](#8-deployment)
9. [Principios de Diseño](#9-principios-de-diseño)

---

## 1. Visión y Modelo de Negocio

### Visión
Plataforma SaaS que permite a operadores comercializar acceso a internet satelital (Starlink Mini) en entornos móviles y remotos: buses interurbanos, playas, eventos temporales, zonas rurales sin infraestructura.

### Modelo B2B2C

```
┌─────────────┐      ┌──────────────┐      ┌────────────┐
│ SUPERADMIN  │──────│  OPERATOR    │──────│  ENDUSER   │
│ JADS Studio │      │ (Tenant)     │      │ (Cliente)  │
└─────────────┘      └──────────────┘      └────────────┘
     │                      │                      │
  Gestiona              Vende                  Compra
  operadores           tickets                tickets
```

**Roles:**
1. **Superadmin** (JADS Studio): Gestión global, aprobación de operadores, métricas
2. **Operator** (Tenant): Empresa que opera nodos Starlink y vende tickets
3. **Enduser**: Usuario final que compra y activa tickets en portal captive

---

## 2. Arquitectura del Sistema

### 2.1 Stack Completo

```
┌────────────────────────────────────────────────────────────┐
│                    JADSlink Cloud                          │
│  (Proxmox 172.21.204.29 o Localhost)                      │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   FastAPI    │  │  PostgreSQL  │  │    Redis     │   │
│  │   Backend    │→ │   Database   │  │   Cache      │   │
│  │   :8000      │  │   :5433      │  │   :6379      │   │
│  └──────┬───────┘  └──────────────┘  └──────────────┘   │
│         │                                                 │
│         ↓                                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │         React Dashboard + Nginx                 │    │
│  │  /dashboard - Operator panel                    │    │
│  │  /admin - Superadmin panel                      │    │
│  │  :80                                            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└───────────────────┬───────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬───────────┐
        │                       │           │
        ↓                       ↓           ↓
   [Field Node]          [Field Node]  [Field Node]
   GL-MT3000             Rasp Pi       GL-MT3000
   Python Agent          Agent         Agent
   Starlink              Starlink      Starlink
   Portal HTML           Portal        Portal
```

### 2.2 Componentes Principales

**Backend API (FastAPI)**
- Autenticación JWT multi-tenant
- CRUD planes, nodos, tickets, sesiones
- Generación de códigos HMAC-SHA256
- QR codes en base64
- Rate limiting con Redis
- Portal captive HTML ultraliviano

**Frontend Dashboard (React)**
- Pages: login, dashboard, plans, nodes, tickets, sessions, admin
- State management con Zustand
- Estilos con TailwindCSS + shadcn/ui
- Mapas con Leaflet

**Database (PostgreSQL 15)**
- Modelos: Tenant, User, Node, Plan, Ticket, Session
- Soft deletes con `deleted_at`
- Índices en campos frecuentes

**Cache & Rate Limiting (Redis 7)**
- Rate limiting (login, register, activate)
- Cache de consultas
- Pub/Sub para alertas

---

## 3. Stack Técnico

### 3.1 Backend

| Componente | Versión | Propósito |
|-----------|---------|----------|
| FastAPI | 0.111+ | Framework async moderno |
| PostgreSQL | 15-alpine | Base de datos |
| Redis | 7-alpine | Cache + rate limit |
| SQLAlchemy | 2.0+ | ORM async |
| Alembic | 1.13+ | Migraciones DB |
| Pydantic | 2.5+ | Validación schemas |
| JWT | 3.3+ | Autenticación |
| Bcrypt | 23.1+ | Hashing passwords |
| APScheduler | 3.10+ | Tareas periódicas |
| QRCode | 7.4+ | Generación QR |

### 3.2 Frontend

| Componente | Versión | Propósito |
|-----------|---------|----------|
| React | 18+ | UI framework |
| Vite | 6+ | Build tool |
| TypeScript | 5+ | Type safety |
| TailwindCSS | 3+ | Estilos |
| shadcn/ui | Latest | Componentes UI |
| Zustand | Latest | State management |
| TanStack Router | Latest | Routing type-safe |
| Leaflet | Latest | Mapas |

### 3.3 Infraestructura

| Componente | Uso |
|-----------|-----|
| Docker | Contenedorización |
| Nginx | Reverse proxy + SPA |
| Docker Compose | Orquestación local |

---

## 4. Modelos de Datos

### 4.1 Tenant (Operador)

```python
class Tenant:
    id: UUID
    name: str                    # "Transportes ABC"
    slug: str                    # URL-safe, unique
    is_active: bool

    # Suscripción SaaS
    plan_tier: PlanTier         # starter, pro, enterprise
    subscription_status: str     # trialing, active, past_due, canceled
    stripe_customer_id: str | None

    # Settings personalizables
    settings: dict              # logo_url, primary_color, ssid, etc

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 4.2 User

```python
class User:
    id: UUID
    tenant_id: UUID | None      # NULL si es superadmin
    email: str (unique)
    hashed_password: str
    full_name: str
    role: str                   # superadmin, operator
    is_active: bool
```

### 4.3 Node (Nodo de Campo)

```python
class Node:
    id: UUID
    tenant_id: UUID
    name: str                   # "Bus 101"
    serial_number: str (unique)

    # Ubicación
    latitude: float | None
    longitude: float | None
    location_name: str | None

    # Estado
    status: str                 # online, offline, maintenance
    last_heartbeat: datetime | None
    api_key: str               # Para autenticación del agent

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 4.4 Plan

```python
class Plan:
    id: UUID
    tenant_id: UUID
    name: str                   # "30 Minutos"
    duration_minutes: int       # 30, 60, 1440
    price_usd: float           # 2.50
    is_active: bool
```

### 4.5 Ticket

```python
class Ticket:
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    node_id: UUID

    code: str (unique)         # "A3K9P2X7" (HMAC-based)
    qr_data: str              # URL o datos QR

    status: str               # pending, active, expired, revoked

    created_at: datetime
    activated_at: datetime | None
    expires_at: datetime | None

    user_ip: str | None
    user_agent: str | None
```

### 4.6 Session

```python
class Session:
    id: UUID
    ticket_id: UUID
    node_id: UUID
    tenant_id: UUID

    status: str               # active, expired, disconnected

    started_at: datetime
    expires_at: datetime
    disconnected_at: datetime | None

    user_ip: str
    data_used_mb: float
```

---

## 5. API Endpoints

### 5.1 Autenticación

| Método | Ruta | Rate Limit |
|--------|------|-----------|
| POST | `/api/v1/auth/login` | 5/min |
| POST | `/api/v1/auth/register` | 5/5min |
| POST | `/api/v1/auth/refresh` | - |
| POST | `/api/v1/auth/logout` | - |

### 5.2 Tenants

| Método | Ruta |
|--------|------|
| GET | `/api/v1/tenants/me` |
| PATCH | `/api/v1/tenants/me` |

### 5.3 Planes

| Método | Ruta |
|--------|------|
| GET | `/api/v1/plans` |
| POST | `/api/v1/plans` |
| PATCH | `/api/v1/plans/{id}` |
| DELETE | `/api/v1/plans/{id}` |

### 5.4 Nodos

| Método | Ruta |
|--------|------|
| GET | `/api/v1/nodes` |
| POST | `/api/v1/nodes` |
| GET | `/api/v1/nodes/{id}/metrics` |
| GET | `/api/v1/nodes/{id}/stream` (SSE) |
| DELETE | `/api/v1/nodes/{id}` |

### 5.5 Tickets

| Método | Ruta |
|--------|------|
| GET | `/api/v1/tickets` |
| POST | `/api/v1/tickets/generate` |
| POST | `/api/v1/tickets/{id}/revoke` |
| POST | `/api/v1/tickets/revoke-multiple` |
| DELETE | `/api/v1/tickets/{id}` |

### 5.6 Sesiones

| Método | Ruta |
|--------|------|
| GET | `/api/v1/sessions` |
| DELETE | `/api/v1/sessions/{id}` |

### 5.7 Admin

| Método | Ruta |
|--------|------|
| GET | `/api/v1/admin/tenants` |
| GET | `/api/v1/admin/overview` |
| GET | `/api/v1/admin/nodes/map` |
| GET | `/api/v1/admin/logo/public` |

---

## 6. Estado Actual (Mayo 2026)

### 🎯 Servidor Proxmox - ✅ OPERACIONAL

```
IP: 172.21.204.29

Servicios:
✅ Dashboard (Nginx)    → http://172.21.204.29/
✅ API (FastAPI)        → http://172.21.204.29:8000/
✅ PostgreSQL           → 172.21.204.29:5433
✅ Redis                → 172.21.204.29:6379

Credenciales de Prueba:
- Admin:    admin@jads.com / admin123456
- Operator: operator@test.com / operator123456
```

### 📊 Endpoints Verificados ✅

```
✅ POST /auth/login                    → JWT
✅ GET  /tickets                       → Lista completa
✅ POST /tickets/generate              → Crea tickets (HTTP 201)
✅ GET  /plans                         → Lista planes
✅ POST /plans                         → Crea plan
✅ GET  /nodes                         → Lista nodos
✅ POST /nodes                         → Crea nodo
✅ GET  /admin/logo/public             → Logo JADSlink
✅ GET  /uploads/app/jadslink.png      → Archivo directo
```

### 🔧 Último Commit (b7e5491)

**Fecha**: 2026-05-04 01:00:49 UTC
**Cambios**:
1. ✅ Fix AttributeError en PlanTier enum
   - Corregir `PlanTier.free` → no existe
   - Usar valores válidos: `starter`, `pro`, `enterprise`
2. ✅ Fix null safety en endpoint `/api/v1/tickets`
   - Agregar checks para `ticket.tenant` y `ticket.plan`
3. ✅ Fix logo endpoint para devolver ruta relativa
   - Permite que Nginx sirva la imagen desde `/uploads/`
4. ✅ Agregar `asyncpg==0.29.*` a requirements.txt
5. ✅ Configurar docker-compose para escuchar en `0.0.0.0`
   - Permite acceso desde red externa
6. ✅ Nginx location block para `/uploads/`
   - Caching 30 días para archivos uploaded

### 🐛 Bugs Resueltos

| Bug | Causa | Solución |
|-----|-------|----------|
| `AttributeError: free` | PlanTier.free no existía | Usar: starter, pro, enterprise |
| `500 /api/v1/tickets` | Null pointer en relationships | Agregar null checks |
| `404 jadslink.png` | Nginx no servía /uploads/ | Agregar location block |
| `ModuleNotFoundError: asyncpg` | Dependencia faltante | Agregar a requirements.txt |

---

## 7. Fases de Desarrollo

### ✅ FASE 1 — Fundación (COMPLETADA)
- [x] Setup Docker Compose
- [x] Modelos SQLAlchemy
- [x] Autenticación JWT
- [x] Endpoints CRUD básicos

### ✅ FASE 2 — Lógica de Negocio (COMPLETADA)
- [x] Generación códigos HMAC
- [x] QR codes base64
- [x] Validación límites
- [x] Portal captive < 40KB

### ✅ FASE 3 — Frontend Dashboard (COMPLETADA)
- [x] Vite + React + TypeScript
- [x] Todas las páginas
- [x] API client
- [x] Theme toggle

### ✅ FASE 4 — Hardening (COMPLETADA)
- [x] Rate limiting Redis
- [x] 19 tests pytest
- [x] APScheduler jobs
- [x] Documentación

### ✅ FASE 5 — Agent de Campo (COMPLETADA)
- [x] Python agent
- [x] Portal captive
- [x] Firewall iptables
- [x] Heartbeat/Métricas
- [x] SQLite cache
- [x] Systemd + OpenWrt

### 🔲 FASE 6 — Stripe (PENDIENTE)
- [ ] Crear productos
- [ ] Webhook handler
- [ ] Actualizar subscription_status
- [ ] Limitar funcionalidades por plan

### 🔲 FASE 7 — Monitoreo (PENDIENTE)
- [ ] Logging JSON
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alertas

### 🔲 FASE 8 — Cloudflare Tunnel (PENDIENTE)
- [ ] Tunnel setup
- [ ] CI/CD GitHub Actions
- [ ] Backups S3
- [ ] SSL automático

### 🔲 FASE 9 — Features Avanzadas (PENDIENTE)
- [ ] Reportes avanzados
- [ ] Tickets promocionales
- [ ] Multi-idioma
- [ ] White-label

### 🔲 FASE 10 — Optimizaciones (PENDIENTE)
- [ ] Cache Redis avanzado
- [ ] Índices PostgreSQL
- [ ] Connection pooling
- [ ] Particionado de tablas

---

## 8. Deployment

### 8.1 Local (Desarrollo)

```bash
git clone https://github.com/adrpinto83/jadslink.git
cd jadslink

cp .env.example .env
# Editar .env si es necesario

docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py

# Acceder
# Dashboard: http://localhost/
# API Docs: http://localhost:8000/docs
```

### 8.2 Proxmox (Actual)

```
IP: 172.21.204.29
- Dashboard:  :80   → http://172.21.204.29/
- API:        :8000 → http://172.21.204.29:8000/
- PostgreSQL: :5433
- Redis:      :6379

Todos los servicios escuchan en 0.0.0.0 (accesible desde la red)
```

### 8.3 Producción (Futuro - FASE 8)

```bash
./deploy.sh
# Cloudflare Tunnel
# SSL automático
# CI/CD
# Backups S3
```

---

## 9. Principios de Diseño

### 9.1 Liviano Primero
Cada dependencia debe justificarse por bajo consumo:
- Agent: < 25MB RAM, < 5% CPU idle
- Portal: < 40KB
- Dashboard bundle: < 500KB gzipped

### 9.2 Async por Defecto
- Todas las rutas async
- SQLAlchemy async
- Redis async
- Evitar bloqueantes en endpoints

### 9.3 Multi-tenant Estricto
- Todos los modelos tienen `tenant_id`
- Queries filtran automáticamente
- Soft deletes con `deleted_at`
- Tests verifican aislamiento

### 9.4 Seguridad
- JWT con expiración (15min access, 7d refresh)
- HMAC-SHA256 para códigos
- Bcrypt para passwords
- Rate limiting
- CORS restrictivo
- SQL injection imposible (ORM)
- Validación Pydantic en inputs

### 9.5 Developer Experience
- Hot reload (Uvicorn --reload)
- Type safety (TypeScript, Pydantic)
- Autodoc FastAPI
- Setup simple (Docker Compose)
- Seed scripts para data demo

---

## 📞 Contacto

**Proyecto**: JADSlink — JADS Studio, Venezuela
**GitHub**: [adrpinto83/jadslink](https://github.com/adrpinto83/jadslink)
**Licencia**: Privado (uso interno JADS Studio)

---

**Versión**: 2.0.0 | **Última Actualización**: Mayo 2026 | **Estado**: FASE 1-5 ✅ Operacional
