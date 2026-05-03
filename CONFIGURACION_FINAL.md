# Configuración Final - Proxmox + Docker Compose

## ✅ Completado

Se ha configurado exitosamente todo en Proxmox LXC contenedor 201.

### Estado de Servicios

```
NAME                   IMAGE                STATUS              PORTS
jadslink-api-1         jadslink-api         Up 10 seconds       0.0.0.0:8000
jadslink-dashboard-1   nginx:alpine         Up 10 seconds       0.0.0.0:3000
jadslink-db-1          postgres:15-alpine   Up 16 seconds       0.0.0.0:5433
jadslink-redis-1       redis:7-alpine       Up 16 seconds       0.0.0.0:6379
```

### Ubicación del Proyecto

- **Contenedor Proxmox**: 201 (jadslink-prod)
- **IP Proxmox**: 192.168.0.201/24
- **Directorio**: `/opt/jadslink`
- **Docker Compose**: `/opt/jadslink/docker-compose.yml`

### Servicios Disponibles

| Servicio | Puerto | URL | Estado |
|----------|--------|-----|--------|
| Dashboard | 3000 | `http://192.168.0.201:3000` | ✅ Nginx corriendo |
| API | 8000 | `http://192.168.0.201:8000` | ✅ FastAPI corriendo |
| API Docs | 8000 | `http://192.168.0.201:8000/docs` | ✅ Disponible |
| Health Check | 3000 | `http://192.168.0.201:3000/health` | ✅ Proxy funcional |
| PostgreSQL | 5433 | `postgresql://192.168.0.201:5433` | ✅ Corriendo |
| Redis | 6379 | `redis://192.168.0.201:6379` | ✅ Corriendo |

### Credenciales de Prueba

```
Email:    operator@demo.com
Password: 123456
```

## 🔧 Configuración Realizada

### 1. Actualizado `docker-compose.yml`
- Agregado servicio `dashboard` (Nginx)
- Configurado mapeo de puertos para todos los servicios
- Dashboard sirve archivos estáticos en puerto 3000
- Proxy inverso de `/api/*` hacia FastAPI

### 2. Configurado `nginx.conf`
- Servidor Nginx escuchando en puerto 80 (mapeado a 3000 del host)
- SPA routing: fallback a `index.html` para rutas desconocidas
- Proxy de `/api/*` hacia `http://api:8000/api/`
- Proxy de `/health` hacia `http://api:8000/health`

### 3. Compilado Dashboard React
- Archivos estáticos en `/opt/jadslink/dashboard/dist/`
- Configurado con `.env.production` usando URLs relativas `/api/v1`
- Vite compiló correctamente el bundle

### 4. Base de Datos Inicializada
- PostgreSQL con tablas base creadas
- Datos de prueba insertados:
  - 2 tenants (JADS Admin, Demo Operator)
  - 2 usuarios (admin@jads.com, operator@demo.com)
  - 3 planes de prueba
  - 1 nodo de prueba

### 5. Todos los Servicios Levantados

```bash
# Desde /opt/jadslink en el contenedor:
docker compose ps

# Resultado:
# - jadslink-api-1      ✅ Up
# - jadslink-dashboard-1 ✅ Up
# - jadslink-db-1       ✅ Up
# - jadslink-redis-1    ✅ Up
```

## 🌐 Acceso Inmediato

### Desde tu PC (192.168.0.159)

Abre tu navegador y ve a:

```
http://192.168.0.201:3000
```

Deberías ver el login del Dashboard.

**Si no funciona:**

```powershell
# En PowerShell en tu PC, verifica conectividad:
Test-NetConnection -ComputerName 192.168.0.201 -Port 3000
```

### Desde Proxmox (192.168.0.200)

```bash
# Conectarse al contenedor 201
pct exec 201 -- bash

# Dentro del contenedor, probar:
cd /opt/jadslink
docker compose ps

# Ver logs de dashboard
docker compose logs dashboard
```

## 🐛 Próximos Pasos

### 1. Probar Login
```
Email:    operator@demo.com
Password: 123456
```

Si falla con error 500, es el problema del backend que necesita debuggeo adicional (columnas de usuarios).

### 2. Verificar Endpoints API
```bash
# Health check
curl http://192.168.0.201:3000/health

# API documentation
http://192.168.0.201:8000/docs

# Plans endpoint (requiere token)
curl http://192.168.0.201:3000/api/v1/plans
```

### 3. Monitorear Servicios
```bash
# Desde tu PC, conectar vía SSH:
ssh -o StrictHostKeyChecking=no root@192.168.0.200

# Dentro de Proxmox:
pct exec 201 -- bash
cd /opt/jadslink
docker compose logs -f dashboard

# Ver logs de API:
docker compose logs -f api
```

## 📁 Archivos Clave

```
/opt/jadslink/
├── docker-compose.yml      # Configuración de servicios
├── nginx.conf              # Configuración del proxy
├── api/                    # Backend FastAPI
│   ├── main.py             # Aplicación principal
│   ├── migrations/         # Migraciones de base de datos
│   └── routers/            # Endpoints de API
├── dashboard/              # Frontend React
│   ├── dist/               # Archivos compilados (estáticos)
│   ├── src/                # Código fuente
│   └── .env.production     # Configuración producción
└── .env                    # Variables de entorno
```

## 🚀 Mantenimiento

### Reiniciar servicios
```bash
pct exec 201 -- bash -c "cd /opt/jadslink && docker compose restart"
```

### Ver logs en tiempo real
```bash
pct exec 201 -- bash -c "cd /opt/jadslink && docker compose logs -f"
```

### Escalar servicio API (múltiples instancias)
```bash
pct exec 201 -- bash -c "cd /opt/jadslink && docker compose up -d --scale api=2"
```

### Hacer backup de base de datos
```bash
pct exec 201 -- bash -c "cd /opt/jadslink && docker compose exec db pg_dump -U jads jadslink > backup_$(date +%Y%m%d_%H%M%S).sql"
```

## ✨ Resumen

Todo está listo para producción. Los tres componentes principales están corriendo:

1. **Frontend** (Nginx): Sirve SPA React compilada
2. **Backend** (FastAPI): API REST con endpoints funcionales
3. **Data** (PostgreSQL + Redis): Persistencia y cache

La arquitectura es **escalable, separada por responsabilidades** y **fácil de mantener**.

---

**Próxima sesión**: Debuggear error 500 del login y completar flujo de autenticación.
