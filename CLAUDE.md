# JADSlink — Arquitectura Completa y Roadmap

**Proyecto**: Plataforma SaaS Multi-tenant de Conectividad Satelital Comercial
**Organización**: JADS Studio — Venezuela
**Principio Rector**: **Liviano Primero** — Cada dependencia debe justificarse por bajo consumo de RAM/CPU

---

## 📋 Índice

1. [Visión y Modelo de Negocio](#1-visión-y-modelo-de-negocio)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Técnico](#3-stack-técnico)
4. [Modelos de Datos](#4-modelos-de-datos)
5. [API Endpoints](#5-api-endpoints)
6. [Fases de Desarrollo](#6-fases-de-desarrollo)
7. [Roadmap Futuro](#7-roadmap-futuro)
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
     │                      │                      │
  Gestiona              Vende                  Compra
  operadores           tickets                tickets
     │                      │                      │
     └──────────────────────┴──────────────────────┘
               Plataforma JADSlink
```

**Roles:**
1. **Superadmin** (JADS Studio): Gestión global, aprobación de operadores, métricas
2. **Operator** (Tenant): Empresa que opera nodos Starlink y vende tickets
3. **Enduser**: Usuario final que compra y activa tickets en portal captive

### Casos de Uso

#### Caso 1: Buses Interurbanos
Operador instala router GL-MT3000 + Starlink Mini en bus. Pasajeros compran tickets de 30min/1hr/1día usando QR codes o portal captive.

#### Caso 2: Playas y Eventos
Operador despliega varios nodos temporales. Usuarios activan tickets escaneando QR o ingresando código.

#### Caso 3: Zonas Rurales
Operador provee conectividad comunitaria. Vende planes prepago por días/semanas.

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama de Alto Nivel

```
┌──────────────────────────────────────────────────────────┐
│                     INTERNET                              │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────┐
│                    JADSlink Cloud                          │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   FastAPI    │  │  PostgreSQL  │  │    Redis     │   │
│  │   Backend    │─→│   Database   │  │   Cache +    │   │
│  │              │  │              │  │  Rate Limit  │   │
│  └──────┬───────┘  └──────────────┘  └──────────────┘   │
│         │                                                 │
│         ↓                                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │         React Dashboard (Vite)                  │    │
│  │  /dashboard - Operator panel                    │    │
│  │  /admin - Superadmin panel                      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└───────────────────┬───────────────────────────────────────┘
                    │ HTTPS API
                    │
        ┌───────────┴───────────┬───────────┐
        │                       │           │
        ↓                       ↓           ↓
┌───────────────┐      ┌───────────────┐  ┌───────────────┐
│   Field Node  │      │  Field Node   │  │  Field Node   │
│   (Agent 1)   │      │   (Agent 2)   │  │   (Agent N)   │
│               │      │               │  │               │
│ • GL-MT3000   │      │ • Raspberry Pi│  │ • GL-MT3000   │
│ • Python Agent│      │ • Python Agent│  │ • Python Agent│
│ • Starlink Mini│     │ • Starlink    │  │ • Starlink    │
│ • Portal HTML │      │ • Portal HTML │  │ • Portal HTML │
│               │      │               │  │               │
└───────┬───────┘      └───────┬───────┘  └───────┬───────┘
        │                      │                  │
        ↓                      ↓                  ↓
    [Usuarios]             [Usuarios]         [Usuarios]
    WiFi Captive           WiFi Captive       WiFi Captive
    Portal                 Portal             Portal
```

### 2.2 Componentes Principales

#### Backend API (FastAPI)
- **Puerto**: 8000
- **Responsabilidades**:
  - Autenticación JWT multi-tenant
  - CRUD de planes, tickets, nodos, sesiones
  - Generación de códigos únicos (HMAC-SHA256)
  - Generación de QR codes (base64)
  - Rate limiting (Redis)
  - Webhooks Stripe
  - Portal captive HTML (ultraliviano)
  - SSE para métricas en tiempo real
  - Backups automáticos PostgreSQL
  - Alertas de nodos offline

#### Frontend Dashboard (React)
- **Puerto**: 5173 (dev) / 8000 (prod via FastAPI static)
- **Páginas**:
  - `/login`, `/register` - Autenticación
  - `/dashboard` - Overview
  - `/dashboard/plans` - Gestión de planes
  - `/dashboard/tickets` - Generación y listado
  - `/dashboard/nodes` - Gestión de nodos + mapa Leaflet
  - `/dashboard/sessions` - Sesiones activas
  - `/dashboard/reports` - Reportes y gráficas
  - `/dashboard/billing` - Suscripciones Stripe
  - `/dashboard/settings` - Configuración tenant
  - `/dashboard/admin` - Panel superadmin

#### Agent (Python - Hardware)
- **Hardware**: GL.iNet GL-MT3000 / Raspberry Pi
- **Responsabilidades**:
  - Servir portal captive HTML (< 40KB)
  - Redirigir usuarios no autenticados
  - Reportar métricas al backend cada 60s
  - Gestionar firewall (iptables)
  - Monitorear conexión Starlink
  - Heartbeat cada 30s

#### Base de Datos (PostgreSQL 15)
- **Puerto**: 5433
- Modelos: Tenant, User, Node, Plan, Ticket, Session, NodeMetric
- Soft deletes con `deleted_at`
- Índices en campos frecuentes (tenant_id, node_id, status)

#### Cache/Rate Limiting (Redis 7)
- **Puerto**: 6379
- **Configuración**: 128MB maxmemory, allkeys-lru
- **Usos**:
  - Rate limiting (login, register, portal activate)
  - Cache de consultas frecuentes (futuro)
  - Pub/Sub para alertas en tiempo real (futuro)

---

## 3. Stack Técnico

### 3.1 Backend

| Tecnología | Versión | Justificación |
|-----------|---------|---------------|
| **Python** | 3.11+ | Performance + asyncio |
| **FastAPI** | 0.115+ | Async nativo, autodoc, validación Pydantic |
| **SQLAlchemy** | 2.0+ | ORM async, migraciones Alembic |
| **PostgreSQL** | 15-alpine | Base de datos robusta, bajo footprint |
| **Redis** | 7-alpine | Rate limiting, cache, bajo consumo |
| **Uvicorn** | Latest | ASGI server de alto rendimiento |
| **Pydantic** | 2.0+ | Validación de datos, schemas |
| **APScheduler** | 3.10+ | Tareas periódicas (backups, alertas) |
| **python-multipart** | Latest | Form data (portal captive) |
| **qrcode** | Latest | Generación QR codes |
| **python-jose** | Latest | JWT tokens |
| **passlib[bcrypt]** | Latest | Hashing passwords |
| **asyncpg** | Latest | Driver PostgreSQL async |
| **aioredis** | Latest | Driver Redis async |
| **pytest + pytest-asyncio** | Latest | Testing |

**Dockerfile**: Multi-stage build, imagen final < 150MB

### 3.2 Frontend

| Tecnología | Versión | Justificación |
|-----------|---------|---------------|
| **React** | 18+ | Componentes declarativos, ecosystem |
| **TypeScript** | 5+ | Type safety |
| **Vite** | 6+ | Build ultra rápido, HMR |
| **TanStack Router** | Latest | Routing type-safe |
| **Zustand** | Latest | State management liviano (2KB) |
| **TailwindCSS** | 3+ | Utility-first, bundle pequeño |
| **shadcn/ui** | Latest | Componentes accesibles, customizables |
| **Leaflet** | Latest | Mapas (más liviano que Google Maps) |
| **Recharts** | Latest | Gráficas para reportes |
| **Lucide React** | Latest | Iconos SVG livianos |

**Build**: Vite optimiza bundle < 500KB gzipped

### 3.3 Agent (Hardware)

| Tecnología | Versión | Justificación |
|-----------|---------|---------------|
| **Python** | 3.9+ | Disponible en OpenWrt/Raspberry Pi OS |
| **Requests** | Latest | HTTP client simple |
| **No frameworks** | - | Solo stdlib para mínimo footprint |
| **iptables wrapper** | - | Control firewall nativo Linux |

**Footprint**: < 20MB RAM, < 5% CPU idle

### 3.4 DevOps

| Herramienta | Uso |
|-------------|-----|
| **Docker Compose** | Orquestación local |
| **Alembic** | Migraciones de base de datos |
| **Cloudflare Tunnel** | Expose local a internet (FASE futura) |
| **GitHub Actions** | CI/CD (futuro) |

---

## 4. Modelos de Datos

### 4.1 Tenant (Operador)

```python
class Tenant:
    id: UUID
    name: str  # "Transportes ABC"
    slug: str  # "transportes-abc" (único, URL-safe)
    is_active: bool  # Requiere aprobación de superadmin

    # Suscripción SaaS
    subscription_status: str  # trialing, active, past_due, canceled
    subscription_plan: str  # starter, growth, enterprise
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    subscription_current_period_end: datetime | None

    # Límites por plan
    max_nodes: int  # 3 (starter), 10 (growth), ilimitado (enterprise)
    max_tickets_per_month: int

    # Personalización portal captive
    logo_url: str | None
    primary_color: str | None  # Hex color
    custom_domain: str | None  # portal.transportesabc.com

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 4.2 User (Operator/Admin)

```python
class User:
    id: UUID
    tenant_id: UUID | None  # NULL si es superadmin
    email: str (unique)
    hashed_password: str
    full_name: str
    role: str  # superadmin, operator
    is_active: bool

    created_at: datetime
    updated_at: datetime
```

### 4.3 Node (Nodo de campo)

```python
class Node:
    id: UUID
    tenant_id: UUID
    name: str  # "Bus 101"
    serial_number: str (unique)  # "SN-ABC-001"

    # Ubicación
    latitude: float | None
    longitude: float | None
    location_name: str | None  # "Ruta Caracas-Maracay"

    # Estado
    status: str  # online, offline, maintenance
    last_heartbeat: datetime | None
    api_key: str  # Para autenticación del agent

    # Métricas actuales (cache)
    current_sessions: int
    total_bandwidth_mb: float

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 4.4 Plan (Ticket)

```python
class Plan:
    id: UUID
    tenant_id: UUID
    name: str  # "30 Minutos"
    duration_minutes: int  # 30, 60, 1440 (1 día)
    price_usd: float  # 2.50
    is_active: bool

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 4.5 Ticket

```python
class Ticket:
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    node_id: UUID  # A qué nodo está asociado

    code: str (unique, indexed)  # "A3K9P2X7" (8 chars, HMAC-based)
    qr_code_base64: str  # QR code en base64

    status: str  # pending, active, expired, revoked

    # Timestamps
    created_at: datetime
    activated_at: datetime | None
    expires_at: datetime | None

    # Trazabilidad
    user_ip: str | None  # IP de quien activó
    user_agent: str | None
```

### 4.6 Session (Sesión activa)

```python
class Session:
    id: UUID
    ticket_id: UUID
    node_id: UUID
    tenant_id: UUID

    status: str  # active, expired, disconnected

    # Control de tiempo
    started_at: datetime
    expires_at: datetime
    disconnected_at: datetime | None

    # Usuario
    user_ip: str
    user_mac: str | None

    # Métricas
    data_used_mb: float
```

### 4.7 NodeMetric (Métricas de campo)

```python
class NodeMetric:
    id: UUID
    node_id: UUID

    # Timestamp
    timestamp: datetime

    # Métricas reportadas por agent
    active_sessions: int
    total_bandwidth_mbps: float
    cpu_usage_percent: float | None
    memory_usage_percent: float | None
    disk_usage_percent: float | None
    starlink_status: str  # connected, disconnected, searching
```

### 4.8 Relaciones

```
Tenant
  └── Users (1:N)
  └── Nodes (1:N)
  └── Plans (1:N)
  └── Tickets (1:N)
  └── Sessions (1:N)

Node
  └── NodeMetrics (1:N)
  └── Tickets (1:N)
  └── Sessions (1:N)

Plan
  └── Tickets (1:N)

Ticket
  └── Session (1:1)
```

---

## 5. API Endpoints

### 5.1 Autenticación (`/api/v1/auth`)

| Método | Ruta | Descripción | Rate Limit |
|--------|------|-------------|-----------|
| POST | `/login` | Login con email/password → JWT | 5/min |
| POST | `/register` | Registro de nuevo operador (requiere aprobación) | 5/5min |
| POST | `/refresh` | Renovar access token con refresh token | - |
| POST | `/logout` | Invalidar refresh token | - |

### 5.2 Tenants (`/api/v1/tenants`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/me` | Info del tenant actual | Operator |
| PATCH | `/me` | Actualizar settings (logo, color, dominio) | Operator |

### 5.3 Planes (`/api/v1/plans`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Listar planes del tenant | Operator |
| POST | `/` | Crear plan | Operator |
| GET | `/{id}` | Detalle de plan | Operator |
| PATCH | `/{id}` | Actualizar plan | Operator |
| DELETE | `/{id}` | Eliminar plan (soft delete) | Operator |

### 5.4 Nodos (`/api/v1/nodes`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Listar nodos del tenant | Operator |
| POST | `/` | Crear nodo → genera api_key | Operator |
| GET | `/{id}` | Detalle de nodo | Operator |
| PATCH | `/{id}` | Actualizar nodo | Operator |
| DELETE | `/{id}` | Eliminar nodo (soft delete) | Operator |
| GET | `/{id}/metrics` | Historial de métricas | Operator |
| GET | `/{id}/stream` | SSE de métricas en tiempo real | Operator |

### 5.5 Tickets (`/api/v1/tickets`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Listar tickets del tenant | Operator |
| POST | `/generate` | Generar N tickets para un nodo + plan | Operator |
| GET | `/{code}` | Detalle de ticket por código | Operator |
| POST | `/{code}/revoke` | Revocar ticket | Operator |

### 5.6 Sesiones (`/api/v1/sessions`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Listar sesiones activas del tenant | Operator |
| GET | `/{id}` | Detalle de sesión | Operator |
| DELETE | `/{id}` | Desconectar sesión manualmente | Operator |

### 5.7 Portal Captive (`/api/v1/portal`)

| Método | Ruta | Descripción | Rate Limit |
|--------|------|-------------|-----------|
| GET | `/` | Página HTML del portal (< 40KB) | - |
| GET | `/plans` | Lista de planes del nodo (HTMX) | - |
| POST | `/activate` | Activar ticket con código | 10/min |
| GET | `/status/{code}` | Estado del ticket | - |

### 5.8 Agent (`/api/v1/agent`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/heartbeat` | Agent reporta que está online | API Key |
| POST | `/metrics` | Agent envía métricas (sessions, bandwidth) | API Key |
| GET | `/config` | Agent obtiene configuración del backend | API Key |

### 5.9 Suscripciones (`/api/v1/subscriptions`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/plans` | Planes SaaS disponibles (starter, growth, enterprise) | Operator |
| POST | `/checkout-session` | Crear sesión de pago Stripe | Operator |
| POST | `/portal-session` | Crear sesión del portal de cliente Stripe | Operator |

### 5.10 Webhooks (`/api/v1/webhooks`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/stripe` | Recibir eventos de Stripe (payment succeeded, canceled) | Stripe signature |

### 5.11 Admin (`/api/v1/admin`)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/tenants` | Listar todos los operadores | Superadmin |
| POST | `/tenants` | Crear operador manualmente | Superadmin |
| GET | `/tenants/{id}` | Detalle de operador | Superadmin |
| PATCH | `/tenants/{id}/approve` | Aprobar tenant pendiente | Superadmin |
| PATCH | `/tenants/{id}/suspend` | Suspender tenant | Superadmin |
| GET | `/overview` | Métricas globales (total tenants, nodos, sesiones) | Superadmin |
| GET | `/nodes/map` | Mapa global de todos los nodos | Superadmin |

---

## 6. Fases de Desarrollo

### ✅ FASE 1 — Fundación (COMPLETADA)

**Objetivo**: Backend funcional, modelos, autenticación, CRUD básico

**Entregables**:
- [x] Setup Docker Compose (api, db, redis)
- [x] Modelos SQLAlchemy (Tenant, User, Node, Plan, Ticket, Session)
- [x] Migraciones Alembic
- [x] Autenticación JWT multi-tenant
- [x] Endpoints auth (login, register, refresh)
- [x] Endpoints CRUD (plans, nodes, tickets, sessions)
- [x] Seed script (superadmin, tenant demo)
- [x] Configuración CORS

**Archivos clave**:
- `api/models/*.py`
- `api/routers/{auth,plans,nodes,tickets,sessions}.py`
- `api/deps.py` (dependencies)
- `api/database.py`
- `api/scripts/seed.py`

---

### ✅ FASE 2 — Lógica de Negocio (COMPLETADA)

**Objetivo**: Servicios core, generación de tickets, activación de sesiones

**Entregables**:
- [x] `ticket_service.py` - Generación códigos HMAC únicos
- [x] Generación QR codes base64
- [x] `session_service.py` - Activación y expiración de sesiones
- [x] Validación de límites de planes (max_nodes, max_tickets)
- [x] Soft deletes (deleted_at)
- [x] Portal captive HTML ultraliviano (< 40KB)
- [x] Endpoints portal (`/api/v1/portal`)

**Archivos clave**:
- `api/services/ticket_service.py`
- `api/services/session_service.py`
- `api/routers/portal.py`
- `api/portal/index.html`

---

### ✅ FASE 3 — Frontend Dashboard (COMPLETADA)

**Objetivo**: Dashboard React completo para operators y superadmin

**Entregables**:
- [x] Setup Vite + React + TypeScript + TailwindCSS
- [x] TanStack Router (rutas type-safe)
- [x] Zustand (auth store, theme store)
- [x] Componentes shadcn/ui (button, card, table, etc)
- [x] Páginas:
  - Login, Register
  - Dashboard (overview)
  - Plans (CRUD)
  - Nodes (CRUD + mapa Leaflet)
  - Tickets (generación + listado con QR)
  - Sessions (listado activas + desconectar)
  - Reports (gráficas Recharts)
  - Billing (integración Stripe)
  - Settings (personalización tenant)
  - Admin (panel superadmin)
- [x] Theme toggle (light/dark)
- [x] API client con fetch + auth interceptor

**Archivos clave**:
- `dashboard/src/pages/*.tsx`
- `dashboard/src/components/layout/DashboardLayout.tsx`
- `dashboard/src/stores/auth.ts`
- `dashboard/src/api/client.ts`

---

### ✅ FASE 4 — Hardening y Producción (COMPLETADA)

**Objetivo**: Rate limiting, tests, backups, alertas

**Entregables**:
- [x] Rate limiting Redis en endpoints críticos:
  - Login (5/min)
  - Register (5/5min)
  - Portal activate (10/min)
- [x] Utility reutilizable `utils/rate_limit.py`
- [x] Tests pytest:
  - test_ticket_service.py (7 tests)
  - test_session_service.py (5 tests)
  - test_rate_limit.py (7 tests)
- [x] Configuración pytest con fixtures (conftest.py)
- [x] APScheduler jobs:
  - Backup automático PostgreSQL (diario)
  - Alertas de nodos offline (cada 5min)
  - Expiración de sesiones (cada 1min)
- [x] Variables .env.example documentadas
- [x] Documentación:
  - TESTING_GUIDE.md
  - api/tests/README.md
  - FASE4_COMPLETE.md

**Archivos clave**:
- `api/utils/rate_limit.py`
- `api/tests/*.py`
- `pytest.ini`
- `TESTING_GUIDE.md`

**Resultado**: 19 tests pasando, rate limiting funcional, sistema production-ready localmente.

---

### ✅ FASE 5 — Agent de Campo (COMPLETADA)

**Objetivo**: Software Python para hardware (GL-MT3000, Raspberry Pi)

**Entregables**:
- [x] Script Python agent (`agent/agent.py`)
- [x] Servir portal captive HTML local (`agent/portal.py`)
- [x] Redirigir usuarios no autenticados (iptables)
- [x] Heartbeat cada 30s → `/api/v1/agent/heartbeat`
- [x] Reportar métricas cada 60s → `/api/v1/agent/metrics`
- [x] Gestionar firewall con iptables (`agent/firewall.py`)
- [x] Configuración via `/api/v1/agent/config`
- [x] Systemd service y OpenWrt init script
- [x] Script de instalación (`install.sh`)
- [x] Cache SQLite para operación offline
- [x] Session manager con expiración automática
- [x] Sincronización bidireccional con backend

**Estructura Final**:
```
agent/
├── agent.py             # Loop principal + coordinación
├── portal.py            # HTTP server captive portal (< 40KB)
├── firewall.py          # Wrapper iptables/nftables
├── session_manager.py   # Activación y expiración de sesiones
├── sync.py              # Comunicación HTTP con backend
├── cache.py             # SQLite cache local
├── config.py            # Configuración desde .env
├── install.sh           # Script de instalación automatizado
├── .env.example         # Template de configuración
├── requirements.txt     # Solo requests + schedule
└── README.md            # Documentación completa
```

**Archivos clave**:
- `agent/agent.py` - Coordinador principal
- `agent/firewall.py` - Gestión iptables (304 líneas)
- `agent/portal.py` - HTTP server (268 líneas)
- `agent/install.sh` - Instalador multi-OS
- `api/routers/agent.py` - Endpoints backend (200 líneas)

**Características implementadas**:
- Footprint: 15-25 MB RAM ✅
- CPU idle: < 5% ✅
- Dependencias mínimas: requests + schedule ✅
- Compatible OpenWrt 22.03+ ✅
- Compatible Raspberry Pi OS ✅
- Operación offline completa ✅
- Portal HTML < 40KB ✅

**Tecnología**:
- iptables para firewall (universal Linux)
- http.server stdlib para portal
- SQLite para cache local
- subprocess para comandos del sistema
- threading para portal en background

---

### 🔲 FASE 6 — Integración Stripe Completa

**Objetivo**: Suscripciones SaaS funcionales con Stripe

**Pendientes**:
- [ ] Crear productos y precios en Stripe
- [ ] Implementar webhook handler completo
- [ ] Actualizar subscription_status en tiempo real
- [ ] Aplicar límites por plan (max_nodes, max_tickets)
- [ ] Portal de cliente Stripe (gestión de suscripción)
- [ ] Emails de confirmación (SendGrid/AWS SES)
- [ ] Dashboard: indicador de uso (tickets generados / límite)
- [ ] Bloquear funcionalidades si plan expirado

**Planes SaaS propuestos**:

| Plan | Precio | Max Nodos | Max Tickets/mes | Features |
|------|--------|-----------|-----------------|----------|
| **Starter** | $29/mes | 3 | 1,000 | Dashboard básico, soporte email |
| **Growth** | $99/mes | 10 | 5,000 | Reportes avanzados, API access |
| **Enterprise** | Custom | Ilimitado | Ilimitado | Whitelabel, soporte prioritario |

---

### 🔲 FASE 7 — Monitoreo y Alertas

**Objetivo**: Observabilidad del sistema

**Pendientes**:
- [ ] Logging estructurado (JSON logs)
- [ ] Agregación de logs (Loki/CloudWatch)
- [ ] Métricas Prometheus
  - Endpoints FastAPI (`/metrics`)
  - Exporter en agents
- [ ] Dashboards Grafana
- [ ] Alertas:
  - Nodo offline > 5 min → Telegram/Email
  - Alto uso de tickets → Upgrade plan
  - Error rate > 5% → Alert
- [ ] Health checks avanzados
- [ ] Tracing distribuido (Jaeger/OpenTelemetry)

---

### 🔲 FASE 8 — Cloudflare Tunnel + Deploy

**Objetivo**: Exponer servidor local a internet de forma segura

**Pendientes**:
- [ ] Configurar Cloudflare Tunnel
- [ ] Script `deploy.sh` automatizado
- [ ] CI/CD con GitHub Actions
- [ ] Backups offsite (S3/Cloudflare R2)
- [ ] SSL automático
- [ ] CDN para assets estáticos
- [ ] Rollback strategy

---

### 🔲 FASE 9 — Features Avanzadas

**Objetivo**: Diferenciadores competitivos

**Pendientes**:
- [ ] Reportes avanzados:
  - Ingresos por nodo/periodo
  - Heatmaps de uso
  - Exportar CSV/Excel
- [ ] Tickets promocionales (códigos de descuento)
- [ ] Planes recurrentes (suscripciones para endusuarios)
- [ ] Multi-idioma (i18n)
- [ ] White-label completo (dominio custom operator)
- [ ] API pública para integraciones
- [ ] Webhooks para operators
- [ ] Mobile app (React Native)

---

### 🔲 FASE 10 — Optimizaciones

**Objetivo**: Escalar a miles de nodos

**Pendientes**:
- [ ] Cache Redis para queries frecuentes
- [ ] Índices PostgreSQL optimizados
- [ ] Connection pooling avanzado
- [ ] Particionado de tablas (metrics, sessions)
- [ ] Read replicas PostgreSQL
- [ ] Load balancing (múltiples instancias API)
- [ ] Redis Cluster
- [ ] Profiling y optimización de queries lentas

---

## 7. Roadmap Futuro

### Q2 2026
- [x] FASE 1-4 completadas
- [x] FASE 5: Agent funcional en campo
- [ ] Piloto con 3 nodos en buses
- [ ] FASE 6: Stripe integrado

### Q3 2026
- [ ] FASE 6: Stripe integrado
- [ ] FASE 7: Monitoreo Grafana
- [ ] 10 operators, 30 nodos

### Q4 2026
- [ ] FASE 8: Cloudflare Tunnel
- [ ] FASE 9: Features avanzadas
- [ ] 50 operators, 150 nodos

### 2027
- [ ] FASE 10: Optimizaciones
- [ ] Expansión regional (LATAM)
- [ ] 500+ operators, 2000+ nodos

---

## 8. Deployment

### 8.1 Ambiente Local (Actual)

```bash
# 1. Clonar repo
git clone git@github.com:adrpinto83/jadslink.git
cd jadslink

# 2. Configurar variables
cp .env.example .env
# Editar .env y generar SECRET_KEY y TICKET_HMAC_SECRET

# 3. Levantar servicios
docker compose up -d

# 4. Ejecutar migraciones
docker compose exec api alembic upgrade head

# 5. Seed inicial (superadmin + tenant demo)
docker compose exec api python scripts/seed.py

# 6. Acceder
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# Dashboard: http://localhost:5173 (después de `cd dashboard && npm run dev`)
```

### 8.2 Producción (Futuro - FASE 8)

**Opción 1: VPS + Cloudflare Tunnel**
```bash
# Servidor local/VPS con IP dinámica
./deploy.sh
# Script automatiza:
# - Docker Compose production
# - Cloudflare Tunnel setup
# - SSL automático
# - Backups S3
```

**Opción 2: Cloud (AWS/GCP/Azure)**
- ECS/Cloud Run para API
- RDS PostgreSQL
- ElastiCache Redis
- CloudFront CDN
- S3 para backups

---

## 9. Principios de Diseño

### 9.1 Liviano Primero

**Justificación**: El agent corre en hardware limitado (GL-MT3000: 580MHz, 256MB RAM)

**Reglas**:
1. Cada dependencia debe justificarse
2. Preferir stdlib sobre librerías pesadas
3. Medir footprint RAM/CPU antes de merge
4. Portal captive < 40KB sin dependencias externas
5. Agent sin frameworks (solo stdlib + requests)

### 9.2 Async por Defecto

**Justificación**: FastAPI async permite manejar miles de requests concurrentes con bajo consumo

**Reglas**:
1. Todas las rutas async
2. SQLAlchemy async
3. Redis async
4. Evitar operaciones bloqueantes en endpoints

### 9.3 Multi-tenant Estricto

**Justificación**: Aislamiento de datos entre operators

**Reglas**:
1. Todos los modelos tienen `tenant_id`
2. Queries siempre filtran por `tenant_id` (excepto superadmin)
3. Dependency `get_current_tenant()` en todas las rutas operator
4. Tests verifican aislamiento

### 9.4 Seguridad Paranoia

**Justificación**: Sistema maneja dinero (tickets) y datos sensibles

**Reglas**:
1. Rate limiting en endpoints públicos
2. HMAC para códigos de tickets (no UUIDs adivinables)
3. API keys rotables para agents
4. Passwords hasheados con bcrypt
5. JWT con expiración corta (15min)
6. Refresh tokens con expiración larga (7 días) pero revocables
7. HTTPS obligatorio en producción
8. Validación Pydantic en todos los inputs
9. SQL injection imposible (SQLAlchemy ORM)
10. CORS restrictivo

### 9.5 Observabilidad

**Justificación**: Detectar problemas antes que usuarios

**Reglas**:
1. Logs estructurados (JSON)
2. Health checks en todos los servicios
3. Métricas expuestas (Prometheus format)
4. Alertas proactivas (nodo offline, error rate)
5. Trazabilidad de tickets (quién, cuándo, desde dónde)

### 9.6 Developer Experience

**Justificación**: Velocidad de desarrollo

**Reglas**:
1. Hot reload en dev (Uvicorn --reload, Vite HMR)
2. Type safety (TypeScript frontend, Pydantic backend)
3. Autodoc (FastAPI /docs, TSDoc)
4. Tests rápidos (SQLite in-memory)
5. Setup simple (Docker Compose)
6. Seed scripts para data demo

---

## 10. Contacto y Contribución

**Proyecto**: JADS Studio — Venezuela
**GitHub**: [github.com/adrpinto83/jadslink](https://github.com/adrpinto83/jadslink)
**Licencia**: Propietary (uso interno JADS Studio)

### Contribuir

1. Fork el repo
2. Crear branch `feature/nombre-feature`
3. Commit con mensajes descriptivos
4. Abrir PR con descripción detallada
5. Tests deben pasar (`pytest tests/ -v`)
6. Review por maintainer

---

## 11. Referencias

### Documentación Técnica
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [React Router](https://reactrouter.com)
- [TailwindCSS](https://tailwindcss.com)

### Documentación del Proyecto
- **README.md**: Inicio rápido
- **TESTING_GUIDE.md**: Guía completa de pruebas
- **FASE4_COMPLETE.md**: Detalles FASE 4
- **api/tests/README.md**: Tests unitarios
- **Este documento (CLAUDE.md)**: Arquitectura completa

---

**Última actualización**: 2026-04-17
**Versión**: 1.1.0
**Estado**: FASE 1-5 completadas ✅ | Sistema production-ready para deployment en campo
