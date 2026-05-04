# JADSlink — Plataforma SaaS Multi-tenant de Conectividad Satelital

**Visión:** Plataforma B2B2C que permite a operadores comercializar acceso a internet satelital (Starlink Mini) en buses, playas, eventos y zonas rurales.

**Modelo de Negocio:**
```
JADS Studio (Superadmin) → Operadores (Tenants) → Usuarios Finales
```

## 🚀 Stack Técnico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| **Backend API** | FastAPI | 0.111+ |
| **Base de Datos** | PostgreSQL | 15-alpine |
| **Cache/Rate Limit** | Redis | 7-alpine |
| **Frontend** | React + Vite | 18+ / 6+ |
| **Estilos** | TailwindCSS | 3+ |
| **Servidor Web** | Nginx | Alpine |
| **Orquestación** | Docker Compose | Latest |

## 📋 Estado Actual

### ✅ Completado
- [x] **FASE 1-5**: Fundación, lógica de negocio, frontend, hardening, agent de campo
- [x] Autenticación JWT multi-tenant
- [x] CRUD de planes, nodos, tickets, sesiones
- [x] Generación de QR codes
- [x] Portal captive HTML ultraliviano
- [x] Dashboard React completo
- [x] Rate limiting con Redis
- [x] Backups automáticos
- [x] Tests unitarios

### 🔄 En Progreso
- [ ] FASE 6: Integración Stripe (suscripciones SaaS)
- [ ] FASE 7: Monitoreo y alertas (Prometheus, Grafana)
- [ ] FASE 8: Cloudflare Tunnel + CI/CD
- [ ] FASE 9: Features avanzadas
- [ ] FASE 10: Optimizaciones

## 🏃 Inicio Rápido

### Requisitos
- Docker & Docker Compose
- Git
- Puerto 80, 8000, 5433, 6379 disponibles

### Setup Local

```bash
# 1. Clonar repositorio
git clone https://github.com/adrpinto83/jadslink.git
cd jadslink

# 2. Configurar variables
cp .env.example .env
# Editar .env y generar SECRET_KEY y TICKET_HMAC_SECRET

# 3. Levantar servicios
docker compose up -d

# 4. Ejecutar migraciones
docker compose exec api alembic upgrade head

# 5. Crear datos de prueba
docker compose exec api python scripts/seed.py

# 6. Acceder
# Dashboard: http://localhost:80/
# API Docs: http://localhost:8000/docs
```

### Credenciales de Prueba

```
Superadmin:
  Email: admin@jads.com
  Pass: admin123456

Operator:
  Email: operator@test.com
  Pass: operator123456
```

## 📍 Acceso Remoto (Proxmox)

```
Dashboard: http://172.21.204.29/
API: http://172.21.204.29:8000/
API Docs: http://172.21.204.29:8000/docs
```

## 📚 Documentación

- **[`CLAUDE.md`](./CLAUDE.md)** — Arquitectura detallada, diseño de base de datos, endpoints, roadmap
- **Docker**: Ver [`docker-compose.yml`](./docker-compose.yml)
- **Backend**: Ver [`api/`](./api/) y [`api/README.md`](./api/README.md)
- **Frontend**: Ver [`dashboard/`](./dashboard/)

## 🔧 Estructura del Proyecto

```
jadslink/
├── api/                          # Backend FastAPI
│   ├── models/                   # SQLAlchemy ORM models
│   ├── routers/                  # API endpoints
│   ├── services/                 # Lógica de negocio
│   ├── schemas/                  # Pydantic schemas
│   ├── middleware/               # CORS, CSRF, etc
│   ├── scripts/                  # seed.py, migrations
│   ├── requirements.txt           # Dependencias Python
│   ├── Dockerfile                # Imagen API
│   └── main.py                   # App FastAPI principal
├── dashboard/                    # Frontend React
│   ├── src/
│   │   ├── pages/               # Rutas principales
│   │   ├── components/          # Componentes React
│   │   ├── stores/              # Zustand state management
│   │   ├── api/                 # Cliente HTTP
│   │   └── hooks/               # Custom hooks
│   ├── package.json             # Dependencias Node
│   └── vite.config.ts           # Config Vite
├── agent/                        # Python agent (hardware)
│   ├── agent.py                 # Loop principal
│   ├── portal.py                # Portal captive HTTP
│   ├── firewall.py              # Gestión iptables
│   └── install.sh               # Instalador
├── docker-compose.yml            # Orquestación servicios
├── nginx.conf                    # Config servidor web
├── .env.example                  # Template variables
├── CLAUDE.md                     # Arquitectura completa
└── README.md                     # Este archivo
```

## 🔑 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/login` — Login
- `POST /api/v1/auth/register` — Registro operator
- `POST /api/v1/auth/refresh` — Renovar token
- `POST /api/v1/auth/logout` — Logout

### Planes
- `GET /api/v1/plans` — Listar planes
- `POST /api/v1/plans` — Crear plan
- `PATCH /api/v1/plans/{id}` — Actualizar
- `DELETE /api/v1/plans/{id}` — Eliminar (soft delete)

### Nodos
- `GET /api/v1/nodes` — Listar nodos
- `POST /api/v1/nodes` — Crear nodo
- `GET /api/v1/nodes/{id}/metrics` — Métricas
- `GET /api/v1/nodes/{id}/stream` — SSE en tiempo real

### Tickets
- `GET /api/v1/tickets` — Listar tickets
- `POST /api/v1/tickets/generate` — Generar lote
- `POST /api/v1/tickets/{id}/revoke` — Revocar
- `POST /api/v1/tickets/revoke-multiple` — Revocar múltiples
- `DELETE /api/v1/tickets/{id}` — Eliminar permanentemente

### Sesiones
- `GET /api/v1/sessions` — Listar activas
- `DELETE /api/v1/sessions/{id}` — Desconectar

### Admin
- `GET /api/v1/admin/tenants` — Listar operators
- `GET /api/v1/admin/overview` — Métricas globales
- `GET /api/v1/admin/nodes/map` — Mapa de nodos

## 🛠️ Comandos Útiles

```bash
# Ver logs
docker compose logs -f api
docker compose logs -f dashboard
docker compose logs -f db

# Acceder a contenedores
docker compose exec api bash
docker compose exec db psql -U postgres

# Ejecutar tests
docker compose exec api pytest tests/ -v

# Recrear volúmenes
docker compose down -v
docker compose up -d

# Limpiar todo
docker compose down
docker system prune -a
```

## 📊 Modelos de Datos

**Tenant** → Usuario → Nodo → Plan → Ticket → Sesión

Ver [CLAUDE.md](./CLAUDE.md#4-modelos-de-datos) para esquema completo.

## 🔐 Seguridad

- ✅ JWT con expiración (15min access, 7días refresh)
- ✅ HMAC-SHA256 para códigos de tickets
- ✅ Bcrypt para contraseñas
- ✅ Rate limiting (Redis)
- ✅ CORS restrictivo
- ✅ SQL injection imposible (SQLAlchemy ORM)
- ✅ Validación Pydantic en todos inputs

## 📈 Monitoreo

```bash
# Health check API
curl http://172.21.204.29:8000/health

# Ver métricas Prometheus (futuro)
curl http://172.21.204.29:8000/metrics
```

## 🚀 Deployment

### Local (Desarrollo)
```bash
docker compose up -d
```

### Proxmox (Actual)
```
IP: 172.21.204.29
- Dashboard: puerto 80
- API: puerto 8000
- PostgreSQL: puerto 5433
- Redis: puerto 6379
```

### Producción (Futuro - FASE 8)
- [ ] Cloudflare Tunnel
- [ ] HTTPS automático
- [ ] CI/CD GitHub Actions
- [ ] Backups en S3
- [ ] Monitoring con Grafana

## 📝 Notas Importantes

1. **Liviano primero** — Cada dependencia debe justificarse por bajo consumo de RAM/CPU
2. **Async por defecto** — FastAPI async para manejar miles de requests concurrentes
3. **Multi-tenant estricto** — Todos los modelos tienen `tenant_id`, queries filtran automáticamente
4. **Soft deletes** — Datos nunca se eliminan (campo `deleted_at`)
5. **Tests obligatorios** — Cualquier feature nueva debe incluir tests

## 🤝 Contribución

1. Fork el repo
2. Crear branch `feature/descripcion`
3. Commit con mensajes descriptivos
4. Tests deben pasar: `pytest tests/ -v`
5. Push y crear PR

## 📞 Contacto

- **Proyecto**: JADSlink — JADS Studio, Venezuela
- **GitHub**: [adrpinto83/jadslink](https://github.com/adrpinto83/jadslink)
- **Licencia**: Privado (uso interno JADS Studio)

---

**Última actualización**: Mayo 2026 | **Versión**: 2.0.0 | **Estado**: FASE 1-5 ✅ Operacional
