# GEMINI.md — JADSlink
# JADS Studio | Plataforma de Conectividad Comercial Satelital
# Versión: 1.0 | Ambiente: LOCAL DEV → Producción futura con Cloudflare Tunnel

---

## 🎯 MISIÓN DEL PROYECTO

JADSlink es una plataforma SaaS (Software as a Service) multi-tenant que permite a empresas (operadores) registrarse, suscribirse y autogestionar la comercialización de acceso a internet satelital (Starlink Mini) en entornos móviles y remotos.

**Modelo de negocio B2B2C:**
- `superadmin` → JADS Studio: visión global, aprueba y gestiona operadores, supervisa la plataforma.
- `operator`   → empresa cliente: se suscribe a un plan, administra sus nodos, personaliza su portal, genera y vende tickets.
- `enduser`    → usuario final: escanea/ingresa código y navega por tiempo pagado.

**Principio rector absoluto: LIVIANO PRIMERO.**
Cada decisión de stack, cada dependencia, cada query debe justificarse por su bajo consumo de RAM, CPU y ancho de banda. Los nodos de campo corren en hardware mínimo. El servidor central correrá en una máquina doméstica con internet NAT.

---

## 🗺️ CONTEXTO DE DESPLIEGUE

### Fase actual: LOCAL
- Todo corre en una sola máquina del desarrollador via Docker Compose
- Acceso local en `http://localhost:8000`
- Base de datos y Redis locales en contenedores

### Fase futura: PRODUCCIÓN (no implementar ahora, solo tener en mente)
- Mismo Docker Compose desplegado en servidor con internet Fibex (NAT)
- Cloudflare Tunnel (`cloudflared`) expondrá el servicio sin IP pública
- Sin Railway, sin VPS — servidor propio = costo $0 de hosting
- El CLAUDE.md se actualizará cuando lleguemos a esa fase

---

## 📁 ESTRUCTURA DEL PROYECTO

Crear y mantener esta estructura desde el inicio. No crear archivos fuera de ella.

```
jadslink/
│
├── CLAUDE.md                        ← este archivo
├── .env                             ← variables locales (no commitear)
├── .env.example                     ← plantilla pública
├── .gitignore
├── docker-compose.yml               ← orquestación local completa
│
├── api/                             ← Backend FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                      ← app FastAPI, routers, CORS, startup
│   ├── config.py                    ← Settings con pydantic-settings
│   ├── database.py                  ← engine async, get_db dependency
│   ├── deps.py                      ← dependencias compartidas (JWT, tenant)
│   │
│   ├── models/                      ← SQLAlchemy ORM
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── tenant.py
│   │   ├── node.py
│   │   ├── plan.py
│   │   ├── ticket.py
│   │   └── session.py
│   │
│   ├── schemas/                     ← Pydantic v2 request/response
│   │   ├── auth.py
│   │   ├── tenant.py
│   │   ├── node.py
│   │   ├── plan.py
│   │   ├── ticket.py
│   │   └── session.py
│   │
│   ├── routers/                     ← Un router por dominio
│   │   ├── auth.py
│   │   ├── tenants.py              ← NEW: para que el operador gestione su tenant
│   │   ├── subscriptions.py        ← NEW: para gestionar pagos y planes SaaS
│   │   ├── webhooks.py             ← NEW: para recibir eventos de Stripe
│   │   ├── nodes.py
│   │   ├── plans.py
│   │   ├── tickets.py
│   │   ├── sessions.py
│   │   ├── metrics.py
│   │   ├── portal.py               ← captive portal endpoints
│   │   ├── agent.py                ← endpoints exclusivos para el agente
│   │   └── admin.py                ← solo superadmin
│   │
│   ├── services/                    ← Lógica de negocio desacoplada
│   │   ├── ticket_service.py        ← generación HMAC, validación
│   │   ├── session_service.py       ← activar, expirar, desconectar
│   │   ├── subscription_service.py  ← NEW: lógica de Stripe
│   │   └── alert_service.py         ← detectar nodos caídos
│   │
│   ├── portal/                      ← Captive portal (HTML estático)
│   │   ├── index.html               ← página única, HTMX, < 40KB total
│   │   └── style.css                ← CSS mínimo inline-able
│   │
│   ├── static/                      ← Build del dashboard (generado)
│   │   └── dash/                    ← React build output
│   │
│   └── migrations/                  ← Alembic
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│
├── dashboard/                       ← Frontend React + Vite
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/                     ← axios client + endpoints tipados
│       │   └── client.ts
│       ├── stores/                  ← Zustand stores
│       │   └── auth.ts
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Register.tsx         ← NEW: para nuevos operadores
│       │   ├── Dashboard.tsx        ← overview general
│       │   ├── Nodes.tsx            ← lista + mapa Leaflet
│       │   ├── NodeDetail.tsx       ← métricas en tiempo real (SSE)
│       │   ├── Tickets.tsx          ← generar, listar, QR
│       │   ├── Sessions.tsx         ← sesiones activas
│       │   ├── Plans.tsx            ← CRUD de planes de tickets
│       │   ├── Settings.tsx         ← NEW: para personalizar el tenant
│       │   ├── Billing.tsx          ← NEW: para gestionar la suscripción
│       │   ├── Reports.tsx          ← ventas por período
│       │   └── Admin.tsx            ← solo superadmin
│       └── components/
│           ├── NodeMap.tsx          ← Leaflet wrapper
│           ├── NodeStatusBadge.tsx
│           ├── TicketQR.tsx
│           └── MetricChart.tsx      ← Recharts wrapper
│
└── agent/                           ← Agente Python de nodo de campo
    ├── requirements.txt             ← SOLO: requests, schedule, routeros-api
    ├── agent.py                     ← entry point
    ├── config.py                    ← lee .env local del nodo
    ├── cache.py                     ← SQLite local (sqlite3 nativo)
    ├── mikrotik.py                  ← wrapper RouterOS API
    ├── sync.py                      ← comunicación HTTPS con servidor
    └── session_manager.py           ← expirar sesiones vencidas
```

---

## ⚙️ STACK TECNOLÓGICO

### Backend `api/` — reglas fijas, no sustituir

```
Framework   : FastAPI 0.111+ (async nativo, OpenAPI automático)
ORM         : SQLAlchemy 2.0 async + Alembic para migraciones
Driver DB   : asyncpg (PostgreSQL) / aiosqlite (tests)
Base datos  : PostgreSQL 15-alpine (contenedor local)
Cache       : Redis 7-alpine — SOLO para: sesiones JWT y rate limiting
              maxmemory 128mb, política allkeys-lru
Auth        : JWT HS256 — access_token 15min / refresh_token 7 días
              Librería: python-jose[cryptography]
Passwords   : passlib[bcrypt]
Validación  : Pydantic v2 (sin extras innecesarios)
Config      : pydantic-settings (lee .env automáticamente)
Tareas      : APScheduler 3.10 — expirar sesiones, alertas de nodos
              NO Celery (demasiado pesado para este caso)
Tiempo real : SSE (Server-Sent Events) para telemetría en dashboard
              NO WebSockets — SSE es más simple y suficiente
Logs        : logging estándar Python → stdout
              Formato: JSON en producción, legible en desarrollo
HTTP client : httpx (async) para llamadas internas si se necesitan
Billing     : Stripe (via `stripe` Python library) para suscripciones
```

### Captive Portal `api/portal/` — reglas de peso máximo

```
Stack       : HTML5 + CSS puro + HTMX 1.9 (desde CDN, ~14KB gzip)
              CERO frameworks JS — CERO npm — CERO build step
Peso total  : < 40KB incluyendo todo
Fuentes     : System fonts únicamente (no cargar Google Fonts)
Imágenes    : SVG inline o base64 pequeño — sin PNGs externos
Funciona en : móviles con señal 2G/3G degradada
Flujo único : WiFi → redirect → ver planes → ingresar código → navegar
```

### Dashboard `dashboard/` — liviano y funcional

```
Framework   : React 18 + Vite (build estático → api/static/dash/)
UI Kit      : shadcn/ui + Tailwind CSS (purge en build — solo clases usadas)
Estado      : Zustand 4 (3KB minificado) — SIN Redux, SIN Context complejo
Fetching    : TanStack Query v5 — cache, refetch, loading states
Mapas       : Leaflet.js — visualización de nodos en mapa
Gráficas    : Recharts — métricas y reportes
Tiempo real : EventSource nativo (SSE) — telemetría de nodos
Build output: npm run build → dist/ → copiar a api/static/dash/
```

### Agente `agent/` — mínimo absoluto

```
Runtime     : Python 3.11 stdlib al máximo
Dependencias: requests, schedule, routeros-api (SOLO estos 3)
Storage     : sqlite3 nativo — cache local de tickets
Comunicación: HTTPS REST al servidor central cada 30 segundos
Modo offline: valida tickets del cache SQLite sin necesidad de internet
Hardware    : GL.iNet GL-MT3000 o Raspberry Pi Zero 2W
Instalación : pip install -r requirements.txt (sin Docker en campo)
```

---

## 🗄️ MODELOS DE BASE DE DATOS

Implementar en `api/models/` en este orden exacto:

```python
# 1. tenant.py
class Tenant(Base):
    __tablename__ = "tenants"
    id                   : UUID  (pk, default uuid4)
    name                 : str   (not null)
    slug                 : str   (unique, usado en URLs)
    is_active            : bool  (default True)
    # Subscription details
    plan_tier            : Enum  ("starter", "pro", "enterprise") default "starter"
    subscription_status  : Enum  ("trialing", "active", "past_due", "canceled", "unpaid") default "trialing"
    stripe_customer_id   : str   nullable (unique)
    # Settings
    settings             : JSON  # {logo_url, primary_color, custom_domain, payment_methods[]}
    created_at           : datetime (default now)

# 2. node.py
class Node(Base):
    __tablename__ = "nodes"
    id           : UUID
    tenant_id    : UUID FK → tenants.id
    name         : str
    serial       : str (unique — impreso en el hardware físico)
    location     : JSON  # {lat, lng, address, description}
    status       : Enum ("online", "offline", "degraded") default "offline"
    last_seen_at : datetime nullable
    api_key      : str (unique — para autenticar el agente, no el JWT)
    config       : JSON  # {ssid, channel, max_clients, bandwidth_default}

# 3. plan.py
class Plan(Base):
    __tablename__ = "plans"
    id                  : UUID
    tenant_id           : UUID FK → tenants.id
    name                : str        # "30 Minutos", "1 Hora", "Día Completo"
    duration_minutes    : int        # 30, 60, 480, 1440, 10080
    price_usd           : Numeric(10,2)
    price_bs            : Numeric(14,2) nullable
    bandwidth_down_kbps : int        # 0 = sin límite
    bandwidth_up_kbps   : int
    max_devices         : int default 1
    is_active           : bool default True

# 4. ticket.py
class Ticket(Base):
    __tablename__ = "tickets"
    id             : UUID
    code           : str(8) UNIQUE   # generado con HMAC, alfanumérico
    qr_data        : str             # URL completa para el QR
    tenant_id      : UUID FK → tenants.id
    node_id        : UUID FK → nodes.id
    plan_id        : UUID FK → plans.id
    status         : Enum ("pending", "active", "expired", "revoked")
    payment_method : Enum ("cash", "mobile_pay", "gateway") default "cash"
    created_at     : datetime
    activated_at   : datetime nullable
    expires_at     : datetime nullable
    device_mac     : str nullable    # registrado al activar

# 5. session.py
class Session(Base):
    __tablename__ = "sessions"
    id          : UUID
    ticket_id   : UUID FK → tickets.id (unique — 1 sesión por ticket)
    node_id     : UUID FK → nodes.id
    device_mac  : str
    ip_address  : str nullable
    started_at  : datetime
    expires_at  : datetime
    bytes_down  : BigInt default 0
    bytes_up    : BigInt default 0
    is_active   : bool default True

# 6. node_metric.py — telemetría liviana, retener solo 7 días
class NodeMetric(Base):
    __tablename__ = "node_metrics"
    id               : UUID
    node_id          : UUID FK → nodes.id
    recorded_at      : datetime (index)
    active_sessions  : int
    bytes_total_day  : BigInt default 0
    signal_quality   : int nullable  # 0-100
    cpu_percent      : float nullable
    ram_percent      : float nullable
```

**Índices obligatorios — crear en migración inicial:**
```sql
CREATE UNIQUE INDEX idx_ticket_code    ON tickets(code);
CREATE INDEX idx_ticket_node_status    ON tickets(node_id, status);
CREATE INDEX idx_session_active        ON sessions(node_id, is_active, expires_at);
CREATE INDEX idx_metric_node_time      ON node_metrics(node_id, recorded_at DESC);
CREATE INDEX idx_node_tenant           ON nodes(tenant_id, status);
CREATE INDEX idx_tenant_slug           ON tenants(slug);
CREATE INDEX idx_tenant_stripe_id      ON tenants(stripe_customer_id);
```

---

## 🔌 API ENDPOINTS

**Prefijo global:** `/api/v1`
**Auth:** Header `Authorization: Bearer <jwt>` en todos excepto `/auth/*`, `/portal/*` y `/webhooks/*`

### `/auth` (público)
```
POST /auth/register           {company_name, email, password} → {status: "pending_approval"}
POST /auth/login              {email, password} → {access_token, refresh_token}
POST /auth/refresh            {refresh_token}   → {access_token}
```

### `/tenants` (rol: operator)
```
GET    /tenants/me             → obtiene el tenant del usuario actual
PATCH  /tenants/me             → actualiza settings {logo_url, primary_color, custom_domain}
```

### `/subscriptions` (público y operator)
```
GET    /subscriptions/plans             (público) → lista de planes de suscripción SaaS
POST   /subscriptions/checkout-session  (operator) {plan_tier} → {session_id}
GET    /subscriptions/portal-session    (operator) → {url} (redirect a portal de Stripe)
```

### `/webhooks` (público, desde Stripe)
```
POST /webhooks/stripe           (recibe eventos de Stripe para actualizar suscripciones)
```

### `/nodes` (rol: operator, superadmin)
```
GET    /nodes/                          lista nodos del tenant
POST   /nodes/                          registrar nodo nuevo
GET    /nodes/{id}                      detalle del nodo
PATCH  /nodes/{id}                      actualizar nombre/config
GET    /nodes/{id}/metrics?hours=24     métricas históricas
GET    /nodes/{id}/stream               SSE — telemetría en tiempo real
                                        evento cada 30s con: status, sessions, bytes
```

### `/plans` (rol: operator, superadmin)
```
GET    /plans/                          planes de tickets del tenant
POST   /plans/                          crear plan de tickets
PATCH  /plans/{id}
DELETE /plans/{id}                      soft delete (is_active=False)
```

### `/tickets` (rol: operator, superadmin)
```
POST   /tickets/generate                {node_id, plan_id, quantity: 1-50}
                                        → [{code, qr_data, qr_base64_png}]
GET    /tickets/                        ?node_id=&status=&date_from=&date_to=
GET    /tickets/{code}
POST   /tickets/{code}/revoke
```

### `/sessions` (rol: operator, superadmin)
```
GET    /sessions/                       ?node_id=&is_active=true
DELETE /sessions/{id}                   desconectar usuario (marca expirado)
```

### `/portal` (sin JWT — autenticación por node_id en query param)
```
GET  /portal/                           HTML del captive portal (HTMX)
GET  /portal/plans/{node_id}            → [{id, name, duration_minutes, price_usd}]
POST /portal/activate                   {code, device_mac, node_id}
                                        → {ok, expires_at, minutes_remaining}
GET  /portal/status/{code}              → {is_active, minutes_remaining}
```

### `/agent` (autenticado por API Key del nodo en header X-Node-Key)
```
POST /agent/heartbeat                   {node_id, metrics: {...}}
                                        servidor actualiza last_seen_at y status
GET  /agent/tickets/sync                → lista de tickets pending/active del nodo
                                        el agente los cachea localmente
POST /agent/sessions/report             reportar activaciones hechas offline
                                        [{code, mac, activated_at}]
```

### `/admin` (rol: superadmin únicamente)
```
GET    /admin/tenants/                    todos los operadores
POST   /admin/tenants/                    crear operador nuevo (manual)
PATCH  /admin/tenants/{id}/approve      aprobar tenant registrado
GET    /admin/overview                    métricas globales consolidadas
GET    /admin/nodes/map                   todos los nodos {id, name, lat, lng, status}
```

### `/health` (público — sin auth)
```
GET  /health                            → {status: "ok", version: "1.0"}
```

---

## 📡 AGENTE DE NODO — LÓGICA CRÍTICA

```python
# agent/agent.py — implementar exactamente así

import schedule, time, logging
from config import AgentConfig
from cache import TicketCache
from mikrotik import MikroTikClient
from sync import ServerSync
from session_manager import SessionManager

log = logging.getLogger("jadslink.agent")

class JADSLinkAgent:
    def __init__(self):
        self.cfg     = AgentConfig()     # lee .env del nodo
        self.cache   = TicketCache()     # SQLite local tickets.db
        self.mt      = MikroTikClient(   # RouterOS API
                           self.cfg.ROUTER_IP,
                           self.cfg.ROUTER_USER,
                           self.cfg.ROUTER_PASS)
        self.sync    = ServerSync(self.cfg)
        self.sessions= SessionManager(self.cache, self.mt)

    def run(self):
        log.info(f"JADSlink Agent iniciado | Nodo: {self.cfg.NODE_ID}")
        schedule.every(30).seconds.do(self._heartbeat)
        schedule.every(5).minutes.do(self._sync_tickets)
        schedule.every(60).seconds.do(self.sessions.expire_overdue)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def activate(self, code: str, mac: str) -> dict:
        """
        Punto de entrada principal — llamado por script MikroTik.
        Funciona con o sin internet (modo offline usando cache local).
        """
        ticket = self.cache.get_ticket(code)

        if not ticket:
            ticket = self.sync.fetch_ticket(code)   # intenta servidor
            if ticket:
                self.cache.store_ticket(ticket)

        if not ticket:
            return {"ok": False, "reason": "ticket_not_found"}

        if ticket["status"] != "pending":
            return {"ok": False, "reason": f"ticket_{ticket['status']}"}

        # Activar en MikroTik Hotspot
        self.mt.add_hotspot_user(
            mac=mac,
            time_limit_minutes=ticket["duration_minutes"],
            rate_down=ticket["bandwidth_down_kbps"],
            rate_up=ticket["bandwidth_up_kbps"]
        )

        self.cache.mark_active(code, mac)
        self.sync.report_activation(code, mac)  # encola si offline

        log.info(f"Ticket {code} activado para {mac}")
        return {"ok": True, "minutes": ticket["duration_minutes"]}

    def _heartbeat(self):
        metrics = {
            "active_sessions" : self.mt.count_active_users(),
            "bytes_total_day" : self.mt.get_bytes_today(),
            "signal_quality"  : self.mt.get_signal_quality(),
        }
        ok = self.sync.post_heartbeat(metrics)
        if not ok:
            log.warning("Servidor no disponible — operando offline")

    def _sync_tickets(self):
        tickets = self.sync.get_pending_tickets()
        if tickets:
            self.cache.bulk_store(tickets)
            log.info(f"{len(tickets)} tickets sincronizados")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    JADSLinkAgent().run()
```

---

## 🐳 DOCKER COMPOSE LOCAL

```yaml
# docker-compose.yml

services:

  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://jads:jadspass@db:5432/jadslink
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      TICKET_HMAC_SECRET: ${TICKET_HMAC_SECRET}
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
      STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET}
      ENVIRONMENT: development
      LOG_LEVEL: INFO
    volumes:
      - ./api:/app        # hot reload en desarrollo
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: jadslink
      POSTGRES_USER: jads
      POSTGRES_PASSWORD: jadspass
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jads -d jadslink"]
      interval: 5s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"       # acceso local para debugging

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    volumes:
      - redisdata:/data
    ports:
      - "6379:6379"       # acceso local para debugging

volumes:
  pgdata:
  redisdata:
```

```dockerfile
# api/Dockerfile

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends 
    libpq5 curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
```

```
# api/requirements.txt — SOLO LO NECESARIO

fastapi==0.111.*
uvicorn[standard]==0.29.*
sqlalchemy[asyncio]==2.0.*
asyncpg==0.29.*
alembic==1.13.*
pydantic-settings==2.2.*
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
redis==5.0.*
apscheduler==3.10.*
stripe==8.*
```

```bash
# .env (nunca commitear — copiar de .env.example)

SECRET_KEY=           # generar: python -c "import secrets; print(secrets.token_hex(32))"
TICKET_HMAC_SECRET=   # generar: python -c "import secrets; print(secrets.token_hex(16))"
STRIPE_SECRET_KEY=    # sk_test_...
STRIPE_WEBHOOK_SECRET=# whsec_...
ENVIRONMENT=development
```

---

## 📏 REGLAS DE CÓDIGO — ABSOLUTAS

### Python — siempre así:
```python
# ✅ CORRECTO
async def get_node(
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
) -> NodeResponse:
    """Retorna nodo validando pertenencia al tenant actual."""
    result = await db.execute(
        select(Node).where(
            Node.id == node_id,
            Node.tenant_id == current_tenant.id  # SIEMPRE filtrar por tenant
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    return NodeResponse.model_validate(node)

# ❌ INCORRECTO — nunca así
def get_node(node_id, db):
    return db.query(Node).filter(Node.id == node_id).first()
```

1. **Type hints** obligatorios en toda función Python
2. **`tenant_id` del JWT** en TODA query — nunca confiar en el body para esto
3. **Pydantic schemas** para toda entrada/salida de API — nunca dicts crudos
4. **async/await** en todos los endpoints FastAPI
5. **Variables de entorno** solo via `pydantic-settings` — cero hardcode
6. **Logs a stdout** únicamente con `logging` estándar — cero prints
7. **Alembic** para toda migración — nunca `Base.metadata.create_all()` en prod
8. **Captive portal**: cero dependencias de red externas en runtime
9. **Sin comentarios obvios** — el código debe ser autoexplicativo
10. **Una responsabilidad por función** — si una función hace dos cosas, dividirla

---

## 🔒 SEGURIDAD — IMPLEMENTAR DESDE EL DÍA 1

```python
# Generación de códigos de ticket — en ticket_service.py
import hmac, hashlib, secrets, base64

def generate_ticket_code(secret: str) -> str:
    """Código de 8 chars alfanumérico con HMAC — no falsificable."""
    random_bytes = secrets.token_bytes(16)
    mac = hmac.new(secret.encode(), random_bytes, hashlib.sha256).digest()
    code = base64.b32encode(mac[:5]).decode().upper()  # 8 chars
    return code

# Rate limiting en portal — en routers/portal.py
# Máximo 10 intentos de activación por IP por minuto
# Usar Redis: INCR key → si > 10, retornar 429

# Multi-tenant aislado — en deps.py
# Todo acceso a datos SIEMPRE pasa por get_current_tenant()
# La función extrae tenant_id del JWT — nunca del body de la request

# API Key de nodo — en deps.py
# Header X-Node-Key: verificar contra nodes.api_key en DB
# Si no coincide → 401, loggear intento

# Ticket single-use — en session_service.py
# Al activar: UPDATE tickets SET status='active' WHERE code=? AND status='pending'
# Si affected_rows == 0 → ya fue activado (race condition protegida)
```

---

## 🚀 ORDEN DE IMPLEMENTACIÓN

Gemini debe seguir este orden. No avanzar a la siguiente fase sin que la anterior funcione y tenga al menos un test básico.

### FASE 1 — Fundación (completar primero)
```
[ ] 1. Estructura de carpetas completa
[ ] 2. docker-compose.yml levanta sin errores
[ ] 3. FastAPI main.py con /health respondiendo
[ ] 4. Modelos SQLAlchemy + migración inicial con Alembic
[ ] 5. Auth JWT: POST /auth/login y /auth/refresh funcionando
[ ] 6. CRUD completo de Nodos con aislamiento multi-tenant
[ ] 7. CRUD completo de Planes
[ ] 8. Generación de Tickets con código HMAC
[ ] 9. Endpoint /portal/activate funcional
[ ] 10. Seed script: 1 superadmin + 1 tenant + 1 nodo + 3 planes de ejemplo
```

### FASE 2 — Portal y Agente
```
[ ] 11. Captive portal HTML+HTMX completo (< 40KB)
[ ] 12. Agente Python: heartbeat + sync de tickets
[ ] 13. Agente Python: modo offline con SQLite cache
[ ] 14. Integración MikroTik API (hotspot users)
[ ] 15. Expiración automática de sesiones (APScheduler)
[ ] 16. Endpoint SSE /nodes/{id}/stream con métricas reales
```

### FASE 3 — Dashboard React
```
[ ] 17. Setup React + Vite + shadcn/ui + Tailwind
[ ] 18. Login y manejo de JWT en cliente
[ ] 19. Página Nodes con mapa Leaflet
[ ] 20. NodeDetail con telemetría SSE en tiempo real
[ ] 21. Página Tickets: generar, mostrar QR, listar
[ ] 22. Página Sessions: sesiones activas, desconectar
[ ] 23. Página Reports: ventas por período y nodo
[ ] 24. Panel Admin: solo visible para superadmin
```

### FASE 4 — Hardening y Producción
```
[ ] 25. Rate limiting Redis en endpoints críticos
[ ] 26. Backup automático PostgreSQL a archivo local
[ ] 27. Alertas de nodo offline (APScheduler → log + futura notif)
[ ] 28. Tests pytest para servicios críticos (ticket, session)
[ ] 29. Documentar variables .env.example completas
[ ] 30. Script deploy.sh para servidor con Cloudflare Tunnel
```

### FASE 5 — SaaS Multi-Tenant Avanzado
```
[ ] 31. Implementar auto-registro de operadores (`POST /auth/register`).
[ ] 32. Añadir endpoint de aprobación de tenants para superadmin.
[ ] 33. Añadir endpoint para que operadores actualicen sus ajustes (`PATCH /tenants/me`).
[ ] 34. Integrar Stripe SDK y añadir endpoints para checkout y portal de cliente.
[ ] 35. Crear webhook para recibir y procesar eventos de Stripe, actualizando `subscription_status`.
[ ] 36. Implementar lógica de "feature gating" (ej. limitar # de nodos) basada en `plan_tier`.
[ ] 37. (Opcional, Pro/Enterprise) Investigar e implementar soporte para dominios personalizados en portales.
```

---

## 💬 PREFIJOS DE TRABAJO

Cuando recibas una instrucción, identifica el área con estos prefijos:

| Prefijo    | Área                                         |
|------------|----------------------------------------------|
| `[API]`    | api/ — FastAPI, routers, services            |
| `[PORTAL]` | api/portal/ — captive portal HTML+HTMX       |
| `[DASH]`   | dashboard/ — React frontend                  |
| `[AGENT]`  | agent/ — agente Python de campo              |
| `[DB]`     | modelos, migraciones Alembic, queries        |
| `[DOCKER]` | docker-compose.yml, Dockerfiles              |
| `[TEST]`   | pytest — tests unitarios e integración       |
| `[SEC]`    | seguridad, rate limiting, validaciones       |
| `[DEPLOY]` | Cloudflare Tunnel, scripts de producción     |
| `[SAAS]`   | Lógica de negocio de suscripciones y tenants |

---

## ⚡ COMANDOS DE DESARROLLO

```bash
# Levantar todo el ambiente local
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f api

# Crear migración nueva
docker compose exec api alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
docker compose exec api alembic upgrade head

# Correr seed de datos de prueba
docker compose exec api python scripts/seed.py

# Build del dashboard (copia a api/static/dash/)
cd dashboard && npm run build && cp -r dist/* ../api/static/dash/

# Acceder a PostgreSQL local
docker compose exec db psql -U jads -d jadslink

# Correr agente localmente (fuera de Docker)
cd agent && python agent.py
```

---

*Proyecto : JADSlink*
*Empresa  : JADS Studio — Venezuela*
*Stack    : FastAPI + HTMX + React + PostgreSQL + Redis*
*Agente   : Python puro → GL.iNet GL-MT3000 / Raspberry Pi*
*Deploy   : Docker Compose local → Cloudflare Tunnel (fase futura)*
*Inicio   : Fase 1 — levantar la fundación*
