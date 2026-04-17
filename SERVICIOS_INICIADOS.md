# JADSlink - Servicios Iniciados ✅

**Fecha**: 2026-04-17 15:07
**Estado**: Todos los servicios funcionando correctamente

---

## 🚀 URLs de Acceso

### Frontend Dashboard
**URL**: http://localhost:5174

- Modo desarrollo con Hot Module Replacement (HMR)
- Cambios en código se reflejan automáticamente
- React DevTools disponible

### Backend API
**URL**: http://localhost:8000

**Documentación Interactiva**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Health Check**: http://localhost:8000/api/v1/health

### Base de Datos PostgreSQL
**Conexión**:
```
Host: localhost
Port: 5433
Database: jadslink
User: jads
Password: jadspass
```

**Cliente GUI recomendado**: pgAdmin, DBeaver, o TablePlus

### Redis
**Conexión**:
```
Host: localhost
Port: 6379
Database: 0
Password: (sin password)
```

**Cliente CLI**:
```bash
docker compose exec redis redis-cli
```

---

## 🔑 Credenciales de Prueba

### Superadmin (Ya creado)
```
Email: admin@jads.io
Password: admin123
Rol: superadmin
```

**Acceso a**:
- Dashboard completo
- Panel de administración
- Gestión de todos los tenants
- Métricas globales

### Crear Operator de Prueba

1. **Ir a**: http://localhost:5174/register
2. **Llenar formulario**:
   - Nombre empresa: "Test Company"
   - Email: test@company.com
   - Password: test12345678
   - Confirmar password: test12345678
3. **Aprobar el tenant** (como superadmin):
   ```bash
   # Opción A: Via SQL
   docker compose exec db psql -U jads -d jadslink -c \
     "UPDATE tenants SET is_active = true WHERE slug = 'test-company';"

   # Opción B: Via API
   # Login como superadmin y usar endpoint /api/v1/admin/tenants/{id}/approve
   ```

---

## 📊 Estado de Servicios

| Servicio | Estado | Puerto | Health Check |
|----------|--------|--------|--------------|
| **Backend API** | ✅ Running | 8000 | `curl http://localhost:8000/api/v1/health` |
| **PostgreSQL** | ✅ Running | 5433 | `docker compose exec db pg_isready` |
| **Redis** | ✅ Running | 6379 | `docker compose exec redis redis-cli PING` |
| **Frontend** | ✅ Running | 5174 | `curl http://localhost:5174` |

---

## 🎯 Flujo de Prueba Rápido

### 1. Login en el Dashboard

```
1. Abrir: http://localhost:5174/login
2. Email: admin@jads.io
3. Password: admin123
4. Click "Iniciar Sesión"
```

### 2. Crear un Plan

```
1. Ir a: /dashboard/plans
2. Click "Nuevo Plan"
3. Llenar:
   - Nombre: Plan 30 Minutos
   - Duración: 30 minutos
   - Precio: 2.50 USD
4. Guardar
```

### 3. Crear un Nodo

```
1. Ir a: /dashboard/nodes
2. Click "Nuevo Nodo"
3. Llenar:
   - Nombre: Nodo Test 001
   - Serial: SN-TEST-001
   - Ubicación: Lat -34.6037, Lng -58.3816
4. Guardar
5. COPIAR el API_KEY generado (necesario para el agent)
```

### 4. Generar Tickets

```
1. Ir a: /dashboard/tickets
2. Seleccionar:
   - Nodo: Nodo Test 001
   - Plan: Plan 30 Minutos
   - Cantidad: 5
3. Click "Generar Tickets"
4. Verificar QR codes
5. Opcional: Imprimir tickets
```

### 5. Ver el Mapa

```
1. Ir a: /dashboard/nodes
2. Ver mapa interactivo (Leaflet)
3. Click en el marcador del nodo
4. Ver popup con información
```

### 6. Cambiar Tema

```
1. Click en botón sol/luna en sidebar
2. Seleccionar:
   - Light (tema claro)
   - Dark (tema oscuro)
   - System (sigue preferencia del sistema)
```

---

## 🛠️ Comandos Útiles

### Ver Logs en Tiempo Real

```bash
# Backend API
docker compose logs api -f

# Base de datos
docker compose logs db -f

# Redis
docker compose logs redis -f

# Frontend (Vite)
tail -f /tmp/claude/-home-adrpinto-jadslink/tasks/bebb0fb.output
```

### Reiniciar Servicios

```bash
# Reiniciar todo
docker compose restart

# Reiniciar solo API
docker compose restart api

# Reiniciar frontend
# Ctrl+C en la terminal del npm run dev, luego npm run dev otra vez
```

### Ejecutar Migraciones

```bash
# Ver migraciones pendientes
docker compose exec api alembic current

# Aplicar migraciones
docker compose exec api alembic upgrade head

# Revertir última migración
docker compose exec api alembic downgrade -1
```

### Ejecutar Tests

```bash
# Tests del backend
docker compose exec api pytest tests/ -v

# Build del frontend (verificar errores)
cd dashboard && npm run build
```

### Consultas a la Base de Datos

```bash
# Entrar a psql
docker compose exec db psql -U jads -d jadslink

# Queries directas
docker compose exec db psql -U jads -d jadslink -c "SELECT * FROM tenants;"
docker compose exec db psql -U jads -d jadslink -c "SELECT * FROM users;"
docker compose exec db psql -U jads -d jadslink -c "SELECT * FROM nodes;"
```

### Redis Commands

```bash
# Entrar a redis-cli
docker compose exec redis redis-cli

# Ver todas las keys
docker compose exec redis redis-cli KEYS "*"

# Ver rate limit keys
docker compose exec redis redis-cli KEYS "rate_limit:*"

# Ver valor de una key
docker compose exec redis redis-cli GET "rate_limit:auth_login:127.0.0.1"
```

---

## 🔥 Endpoints API Más Usados

### Autenticación

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@jads.io","password":"admin123"}'

# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name":"Test Company",
    "email":"test@company.com",
    "password":"test12345678"
  }'

# Refresh Token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

### Gestión (requiere JWT token)

```bash
# Obtener token primero
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@jads.io","password":"admin123"}' | jq -r '.access_token')

# Listar nodos
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/nodes

# Listar planes
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/plans

# Listar tickets
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/tickets

# Obtener info del tenant actual
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/tenants/me
```

---

## 🐛 Troubleshooting

### Frontend no carga

**Problema**: Página en blanco o error
**Solución**:
```bash
# Ver logs de Vite
tail -f /tmp/claude/-home-adrpinto-jadslink/tasks/bebb0fb.output

# Verificar que no haya errores
# Si hay errores, detener y reiniciar
# Ctrl+C y luego: cd dashboard && npm run dev
```

### Backend error 500

**Problema**: API responde con error interno
**Solución**:
```bash
# Ver logs detallados
docker compose logs api -f

# Verificar conexión a DB
docker compose exec db pg_isready -U jads

# Verificar Redis
docker compose exec redis redis-cli PING
```

### No puedo hacer login

**Problema**: Credenciales no funcionan
**Solución**:
```bash
# Verificar que exista el superadmin
docker compose exec db psql -U jads -d jadslink -c \
  "SELECT email, role FROM users WHERE role='superadmin';"

# Si no existe, ejecutar seed:
docker compose exec api python scripts/seed.py
```

### Puerto ya en uso

**Problema**: "Port 5174 is in use"
**Solución**:
```bash
# Ver qué proceso usa el puerto
lsof -i :5174

# Matar el proceso
kill -9 <PID>

# O cambiar el puerto en package.json:
# "dev": "vite --port 5175"
```

---

## 📱 Acceso desde Otros Dispositivos

Para acceder al dashboard desde otro dispositivo en la misma red:

1. **Obtener IP del servidor**:
```bash
hostname -I | awk '{print $1}'
# Ejemplo: 192.168.1.100
```

2. **Modificar vite.config.ts**:
```typescript
server: {
  host: '0.0.0.0',  // Agregar esta línea
  proxy: {
    "/api": {
      target: "http://localhost:8000",
      changeOrigin: true,
    },
  },
}
```

3. **Reiniciar frontend**:
```bash
# Detener con Ctrl+C
npm run dev
```

4. **Acceder desde otro dispositivo**:
```
http://192.168.1.100:5174
```

---

## 🎨 Personalización del Tema

Los colores del dashboard se pueden personalizar en:

**Archivo**: `dashboard/src/globals.css`

```css
@layer base {
  :root {
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    /* ... más variables ... */
  }

  .dark {
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    /* ... más variables ... */
  }
}
```

---

## 📚 Documentación Adicional

- **Arquitectura Completa**: [CLAUDE.md](./CLAUDE.md)
- **Guía del Frontend**: [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md)
- **Guía de Pruebas**: [TESTING_GUIDE.md](./TESTING_GUIDE.md)
- **Estado Completo**: [ESTADO_COMPLETO.md](./ESTADO_COMPLETO.md)
- **FASE 4**: [api/FASE4_COMPLETE.md](./api/FASE4_COMPLETE.md)
- **FASE 5**: [FASE5_COMPLETE.md](./FASE5_COMPLETE.md)

---

## 🎯 Próximos Pasos Sugeridos

1. **Explorar el Dashboard**
   - Crear plans, nodes, tickets
   - Ver el mapa interactivo
   - Probar el cambio de tema

2. **Probar la API**
   - Usar Swagger UI: http://localhost:8000/docs
   - Probar endpoints con curl
   - Ver los logs en tiempo real

3. **Instalar un Agent**
   - Ver [agent/README.md](./agent/README.md)
   - Copiar API_KEY de un nodo
   - Instalar en hardware de prueba

4. **Integrar Stripe**
   - Configurar productos en Stripe
   - Agregar STRIPE_SECRET_KEY al .env
   - Probar checkout flow

---

## 📞 Soporte

**Proyecto**: JADS Studio — Venezuela
**GitHub**: [github.com/adrpinto83/jadslink](https://github.com/adrpinto83/jadslink)

---

**¡Todo está listo para usar! 🚀**

Accede a: **http://localhost:5174**
Login con: **admin@jads.io** / **admin123**
