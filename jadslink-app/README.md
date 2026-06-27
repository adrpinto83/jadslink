# jadslink-app

Aplicación **en producción** de `https://link.jadsstudio.com` — el panel de gestión
de hotspots/routers OpenWrt en campo ("JADSLink - Acceso WiFi").

> ⚠️ Es un codebase **independiente** del resto del repo (`/api`, `/dashboard`, `/agent`).
> Es una versión simplificada (FastAPI + SQLite + SPA vanilla) desplegada en
> Hostinger. Esta carpeta es la copia versionada de lo que corre en el servidor.

## Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite (`uvicorn`)
- **Frontend**: SPA estática (`frontend/`, HTML/CSS/JS vanilla) servida por el backend
- **Auth**: tokens en memoria (`TOKENS` dict) — login admin (`/api/auth/login`)

## Estructura

```
api/
  main.py            # App FastAPI + lifespan (seed_admin + seed_devices)
  database.py        # Engine SQLite (DATABASE_URL o ./data/hotspot.db por defecto)
  models.py          # Device, Client, Code, Report, Command, AdminUser
  routes/
    auth.py          # login/logout/change-password + seed_admin
    devices.py       # /api/devices: heartbeat de agentes + admin + SEED_DEVICES
    codes.py         # códigos de acceso WiFi
frontend/            # SPA + assets estáticos
passenger_wsgi.py    # Entry point WSGI (a2wsgi envuelve la app ASGI) — para Passenger
requirements.txt
deploy/hostinger/    # Artefactos de deployment (ver abajo)
```

## Desarrollo local

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # editar JWT_SECRET
uvicorn api.main:app --reload --port 8000
# http://localhost:8000  (admin / admin123 por defecto — cambiar en prod)
```

## Modelo de agente (routers en campo)

Cada router OpenWrt corre un agente que reporta cada ~30-60s:

```
POST /api/devices/{device_id}/heartbeat     header: X-API-Key: <api_key>
```

El backend valida `api_key` contra la tabla `devices`. **Si la BD SQLite se
recrea (redeploy), la fila del agente desaparece y el heartbeat da 401** → el
dispositivo aparece offline.

**Solución implementada**: `SEED_DEVICES` en `api/routes/devices.py` + `seed_devices(db)`
llamado en el `lifespan` de `main.py`. En cada arranque se reinserta el device del
agente (o se corrige su api_key). Para añadir otro router, agregar su `id` + `api_key`
a `SEED_DEVICES`.

## Deployment en Hostinger

Hosting compartido con LiteSpeed. Limitaciones encontradas: sin `crontab` por SSH,
`shell_exec` deshabilitado en PHP, Passenger Python no funciona en subdirectorios.

**Arquitectura en producción:**

```
Cloudflare → LiteSpeed → public_html/link/index.php (proxy PHP + auto-heal)
           → uvicorn 127.0.0.1:58765 → FastAPI (~/jadslink-app)
```

- `deploy/hostinger/link/index.php` — reverse proxy que además **auto-repara**:
  si uvicorn no escucha en el puerto 58765, lo relanza con `proc_open` + `setsid`
  (con `flock` para no duplicar procesos). Recuperación ~1.7s.
- `deploy/hostinger/link/.htaccess` — desactiva Passenger del dominio padre y
  enruta todo a `index.php`.

Arranque manual de uvicorn en el servidor (si hiciera falta):

```bash
cd ~/jadslink-app
setsid venv/bin/python3.11 -m uvicorn api.main:app --host 127.0.0.1 --port 58765 \
  >> uvicorn.log 2>&1 < /dev/null &
```
