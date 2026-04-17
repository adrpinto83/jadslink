# Guía de Pruebas JADSlink - Frontend + Backend

## 🚀 Inicio Rápido

### 1. Verificar que servicios estén corriendo

```bash
docker compose ps
# Debe mostrar: api (puerto 8000), db (puerto 5433), redis (puerto 6379)

# Verificar API
curl http://localhost:8000/api/v1/health
```

### 2. Levantar Dashboard en modo desarrollo

```bash
cd dashboard
npm install  # Si no se ha hecho antes
npm run dev
```

El dashboard estará disponible en: **http://localhost:5173**

---

## 🧪 Flujo de Pruebas Completo

### PASO 1: Registro de Operador

**URL**: http://localhost:5173/register

**Datos de prueba**:
- Nombre empresa: `Test Company`
- Email: `test@company.com`
- Password: `test12345678`
- Confirmar password: `test12345678`

**Resultado esperado**:
- Mensaje: "Tu cuenta ha sido creada y está pendiente de aprobación"
- Estado en BD: `Tenant.is_active = False`, `subscription_status = trialing`

---

### PASO 2: Aprobar Tenant (como Superadmin)

**Opción A - Via API directamente**:
```bash
# 1. Login como superadmin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@jads.io", "password": "admin123"}'

# Copiar el access_token

# 2. Listar tenants pendientes
curl http://localhost:8000/api/v1/admin/tenants \
  -H "Authorization: Bearer <access_token>"

# 3. Aprobar tenant (necesitarás implementar este endpoint o hacerlo via BD)
```

**Opción B - Via Base de Datos**:
```bash
docker compose exec db psql -U jads -d jadslink -c "UPDATE tenants SET is_active = true WHERE slug = 'test-company';"
```

---

### PASO 3: Login

**URL**: http://localhost:5173/login

**Credenciales operator**:
- Email: `test@company.com`
- Password: `test12345678`

**Credenciales superadmin** (ya existente):
- Email: `admin@jads.io`
- Password: `admin123`

**Resultado esperado**:
- Redirección a `/dashboard`
- Token JWT almacenado en localStorage
- Sidebar visible con todas las opciones

---

### PASO 4: Crear Planes de Tickets

**URL**: http://localhost:5173/dashboard/plans

**Acciones**:
1. Click en "Nuevo Plan"
2. Completar formulario:
   - Nombre: `Plan 30 Minutos`
   - Duración: `30` minutos
   - Precio: `2.50` USD
3. Click "Crear"
4. Repetir para crear planes de 60 min y 1 día

**Endpoints testeados**:
- `GET /api/v1/plans` - Listar planes
- `POST /api/v1/plans` - Crear plan
- `PATCH /api/v1/plans/{id}` - Actualizar plan
- `DELETE /api/v1/plans/{id}` - Eliminar plan (soft delete)

**Verificaciones**:
- [ ] Planes aparecen en tabla
- [ ] Se pueden editar
- [ ] Se pueden eliminar (status cambia a inactivo)
- [ ] Duración se formatea correctamente (30 min, 1 hr, 1 día)

---

### PASO 5: Configuración del Tenant

**URL**: http://localhost:5173/dashboard/settings

**Acciones**:
1. Ver información de la cuenta (nombre, slug, plan, estado)
2. Personalizar:
   - URL del logo: `https://via.placeholder.com/150`
   - Color primario: `#10b981` (verde)
   - Dominio personalizado: `portal.testcompany.com`
3. Click "Guardar Cambios"

**Endpoints testeados**:
- `GET /api/v1/tenants/me` - Obtener tenant actual
- `PATCH /api/v1/tenants/me` - Actualizar settings

**Verificaciones**:
- [ ] Información se muestra correctamente
- [ ] Cambios se guardan
- [ ] Mensaje de éxito aparece
- [ ] Color picker funciona

---

### PASO 6: Gestión de Suscripción (Billing)

**URL**: http://localhost:5173/dashboard/billing

**Nota**: Esta funcionalidad requiere configuración de Stripe

**Endpoints testeados**:
- `GET /api/v1/subscriptions/plans` - Listar planes SaaS
- `POST /api/v1/subscriptions/checkout-session` - Crear sesión de pago
- `GET /api/v1/subscriptions/portal-session` - Portal de cliente Stripe

**Verificaciones**:
- [ ] Estado de suscripción se muestra
- [ ] Límites del plan se muestran correctamente
- [ ] Planes disponibles se listan (requiere Stripe configurado)

**Sin Stripe configurado**:
- Verás el estado pero no podrás crear checkout sessions

---

### PASO 7: Crear Nodo

**URL**: http://localhost:5173/dashboard/nodes

**Datos de prueba**:
- Nombre: `Nodo Test Bus 101`
- Serial: `SN-TEST-001`
- Ubicación: Lat `-34.6037`, Lng `-58.3816` (Buenos Aires)

**Endpoints testeados**:
- `GET /api/v1/nodes` - Listar nodos
- `POST /api/v1/nodes` - Crear nodo
- `GET /api/v1/nodes/{id}` - Detalle del nodo
- `PATCH /api/v1/nodes/{id}` - Actualizar nodo
- `GET /api/v1/nodes/{id}/stream` - SSE métricas en tiempo real

---

### PASO 8: Generar Tickets

**URL**: http://localhost:5173/dashboard/tickets

**Acciones**:
1. Seleccionar nodo
2. Seleccionar plan
3. Cantidad: `5` tickets
4. Click "Generar"

**Endpoints testeados**:
- `POST /api/v1/tickets/generate` - Generar tickets
- `GET /api/v1/tickets` - Listar tickets
- `GET /api/v1/tickets/{code}` - Detalle de ticket
- `POST /api/v1/tickets/{code}/revoke` - Revocar ticket

**Verificaciones**:
- [ ] Códigos únicos de 8 caracteres
- [ ] QR codes se generan
- [ ] Status = pending

---

### PASO 9: Activar Ticket (Portal Captive)

**URL**: http://localhost:8000/api/v1/portal/

**Acciones**:
1. Abrir portal en navegador
2. Ingresar código de ticket generado
3. Click "Activar"

**Endpoints testeados**:
- `GET /api/v1/portal/` - Página HTML del portal
- `GET /api/v1/portal/plans?node_id={uuid}` - Planes del nodo (HTMX)
- `POST /api/v1/portal/activate` - Activar ticket
- `GET /api/v1/portal/status/{code}` - Estado del ticket

**Verificaciones con rate limiting**:
- [ ] Máximo 10 activaciones por minuto por IP
- [ ] Después de 10 intentos: HTTP 429
- [ ] Rate limit se resetea después de 60 segundos

---

### PASO 10: Ver Sesiones Activas

**URL**: http://localhost:5173/dashboard/sessions

**Endpoints testeados**:
- `GET /api/v1/sessions` - Listar sesiones
- `DELETE /api/v1/sessions/{id}` - Desconectar sesión

**Verificaciones**:
- [ ] Sesión activada aparece
- [ ] Tiempo restante se muestra
- [ ] Se puede desconectar manualmente

---

### PASO 11: Reportes

**URL**: http://localhost:5173/dashboard/reports

**Verificaciones**:
- [ ] Filtros por fecha funcionan
- [ ] Gráficas se renderizan
- [ ] Datos de ventas se muestran

---

### PASO 12: Panel Admin (solo superadmin)

**URL**: http://localhost:5173/dashboard/admin

**Login como**: `admin@jads.io` / `admin123`

**Endpoints testeados**:
- `GET /api/v1/admin/tenants` - Todos los operadores
- `POST /api/v1/admin/tenants` - Crear operador manual
- `PATCH /api/v1/admin/tenants/{id}/approve` - Aprobar tenant
- `GET /api/v1/admin/overview` - Métricas globales
- `GET /api/v1/admin/nodes/map` - Mapa global de nodos

---

## 🧪 Testing de Rate Limiting

### Auth Login
```bash
# Debe permitir 5 intentos, luego HTTP 429
for i in {1..7}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "wrong@test.com", "password": "wrong"}'
  echo "Attempt $i"
done
```

### Auth Register
```bash
# Debe permitir 5 registros cada 5 minutos
for i in {1..7}; do
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"company_name\": \"Test $i\", \"email\": \"test$i@test.com\", \"password\": \"test12345678\"}"
  echo "Attempt $i"
done
```

### Portal Activate
```bash
# Debe permitir 10 activaciones por minuto
for i in {1..12}; do
  curl -X POST http://localhost:8000/api/v1/portal/activate \
    -F "code=TESTCODE" \
    -F "node_id=00000000-0000-0000-0000-000000000000"
  echo "Attempt $i"
done
```

---

## ✅ Checklist de Funcionalidades

### Autenticación
- [ ] Registro de operador funciona
- [ ] Login funciona
- [ ] Refresh token funciona
- [ ] Logout limpia tokens
- [ ] Rate limiting en login (5/min)
- [ ] Rate limiting en register (5/5min)

### Planes
- [ ] Crear plan
- [ ] Listar planes
- [ ] Editar plan
- [ ] Eliminar plan (soft delete)
- [ ] Validación de datos

### Settings
- [ ] Ver info del tenant
- [ ] Actualizar logo
- [ ] Actualizar color primario
- [ ] Actualizar dominio custom
- [ ] Cambios se reflejan

### Billing
- [ ] Ver estado de suscripción
- [ ] Ver límites del plan
- [ ] Listar planes disponibles
- [ ] (Opcional) Crear checkout session Stripe
- [ ] (Opcional) Abrir portal Stripe

### Nodos
- [ ] Crear nodo
- [ ] Listar nodos
- [ ] Ver detalle de nodo
- [ ] Actualizar nodo
- [ ] Ver métricas en tiempo real (SSE)
- [ ] Mapa Leaflet funciona

### Tickets
- [ ] Generar tickets
- [ ] Ver lista de tickets
- [ ] Ver QR codes
- [ ] Revocar ticket
- [ ] Filtros funcionan

### Portal Captive
- [ ] Página HTML carga (<40KB)
- [ ] Listar planes del nodo
- [ ] Activar ticket
- [ ] Ver status de ticket
- [ ] Rate limiting (10/min)

### Sesiones
- [ ] Listar sesiones activas
- [ ] Desconectar sesión
- [ ] Ver tiempo restante
- [ ] Filtros funcionan

### Admin
- [ ] Solo visible para superadmin
- [ ] Listar todos los tenants
- [ ] Aprobar tenants
- [ ] Ver métricas globales

---

## 🐛 Troubleshooting

### Dashboard no carga
```bash
# Verificar que el dev server esté corriendo
cd dashboard
npm run dev
```

### API no responde
```bash
docker compose logs api -f
docker compose restart api
```

### Redis no funciona
```bash
docker compose logs redis -f
docker compose restart redis
```

### Base de datos no conecta
```bash
docker compose exec db psql -U jads -d jadslink
# Si falla, revisar logs:
docker compose logs db -f
```

### CORS errors
Verificar que `CORS allow_origins` en `main.py` incluya `http://localhost:5173`

---

## 📊 Monitoreo durante pruebas

### Ver logs de la API en tiempo real
```bash
docker compose logs api -f
```

### Ver queries a PostgreSQL
```bash
docker compose logs db -f | grep SELECT
```

### Ver operaciones de Redis
```bash
docker compose exec redis redis-cli MONITOR
```

### Ver métricas de rate limiting
```bash
docker compose exec redis redis-cli KEYS "rate_limit:*"
docker compose exec redis redis-cli GET "rate_limit:portal_activate:127.0.0.1"
```

---

## 🎯 Resultado Esperado

Al completar todas las pruebas, deberías tener:

✅ Operador registrado y aprobado
✅ Al menos 3 planes creados
✅ Settings personalizados
✅ Al menos 1 nodo creado
✅ Tickets generados con QR codes
✅ Al menos 1 sesión activa
✅ Rate limiting funcionando en 3 endpoints
✅ Portal captive operacional

**JADSlink FASE 1-4 completamente funcional** 🚀
