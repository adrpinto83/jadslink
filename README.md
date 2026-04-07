# JADSlink — Plataforma de Conectividad Comercial Satelital

**Visión:** Plataforma SaaS multi-tenant que permite a operadores comercializar acceso a internet satelital (Starlink Mini) en entornos móviles y remotos: buses, playas, eventos, zonas rurales.

**Modelo:** B2B2C — superadmin → operator → enduser

**Stack:**
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: React + Vite + Tailwind
- Agent: Python puro en hardware mínimo (GL.iNet GL-MT3000 / Raspberry Pi)
- Deploy: Docker Compose local → Cloudflare Tunnel (fase futura)

## Inicio rápido

```bash
# Setup
git clone git@github.com:adrpinto83/jadslink.git
cd jadslink
cp .env.example .env

# Levantar ambiente
docker compose up -d

# Crear migraciones
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py

# API disponible en http://localhost:8000
# Dashboard en http://localhost:8000/dashboard (después de build)
```

## Documentación

- Ver [`CLAUDE.md`](./CLAUDE.md) para arquitectura detallada, stack y orden de implementación
- Fase actual: **Fase 1 — Fundación**

## Contacto

- Proyecto: JADS Studio — Venezuela
- Principio rector: **Liviano primero** — cada dependencia debe justificarse por bajo consumo de RAM/CPU
