# Guía de Testing Manual - Panel de Gestión de Tenants

**Versión**: 1.0.0
**Última actualización**: 2026-04-30

---

## 📋 Requisitos Previos

- JADSlink API corriendo en `http://localhost:8000`
- Dashboard React corriendo en `http://localhost:5173`
- Base de datos con seed data (superadmin, tenants, nodos, tickets)

---

## 🚀 Paso 1: Verificar que el Servidor esté Activo

```bash
# Terminal 1: API
docker compose up -d
curl http://localhost:8000/docs  # Debería cargar Swagger

# Terminal 2: Dashboard (si necesitas)
cd dashboard
npm run dev
# Accesible en http://localhost:5173
```

---

## 🔐 Paso 2: Login como Superadmin

1. Navega a `http://localhost:5173/login`
2. Ingresa:
   - **Email**: `admin@jads.com`
   - **Contraseña**: `admin123456`
3. Click en "Ingresar"
4. Deberías ver el dashboard principal

---

## 📊 Paso 3: Navegar a Panel de Administración

1. En el sidebar izquierdo, haz click en **"Admin"**
2. Deberías ver 6 cards:
   - ✅ Gestión de Pagos
   - ✅ Configuración de Precios
   - ⚠️ Análisis Global (disabled)
   - ✅ **Gestión de Tenants** (NUEVO - habilitado)
   - ✅ Gestión de Empleados
   - ✅ Suscripciones Gratuitas
3. Click en la card **"Gestión de Tenants"**

---

## 🎯 Paso 4: Verificar Estadísticas Globales

Deberías ver 4 stat cards en la parte superior:

### Card 1: "Total Tenants"
- Mostrar cantidad total de tenants
- Describir cuántos están activos
- Ejemplo: "12 (10 activos)"

### Card 2: "Nodos Globales"
- Mostrar total de nodos en la plataforma
- Describir cuántos están online
- Ejemplo: "45 (38 online)"
- Color verde si hay nodos online, rojo si todos offline

### Card 3: "Tickets"
- Mostrar total de tickets generados
- Ejemplo: "1,234"

### Card 4: "Sesiones Activas"
- Mostrar número de sesiones activas en tiempo real
- Ejemplo: "7"
- Color verde si hay sesiones, naranja si cero

---

## 📌 Paso 5: Seleccionar un Tenant

1. Debajo de los stat cards, encontrarás un **dropdown** con etiqueta "Seleccionar Operador"
2. Haz click en el dropdown
3. Deberías ver una lista de tenants disponibles
4. Cada item muestra:
   - Nombre del tenant
   - Badge con plan (free, basic, standard, pro)
   - Badge rojo si está inactivo
5. Selecciona un tenant que tenga nodos/tickets
   - **Recomendación**: Usa el tenant demo creado por seed data

---

## 📈 Paso 6: Verificar Stats del Tenant Seleccionado

Una vez seleccionado un tenant, debajo aparecerán **5 stat cards**:

### Card 1: "Nodos"
- Mostrar `nodes_total`
- Descripción: "N online"
- Ejemplo: "3 (2 online)"

### Card 2: "Tickets"
- Mostrar `tickets_total`
- Descripción: "N activos"
- Ejemplo: "45 (12 activos)"

### Card 3: "Sesiones"
- Mostrar `sessions_active`
- Ejemplo: "2"

### Card 4: "Ingresos"
- Mostrar revenue estimado
- Formato: `$X.XX`
- Ejemplo: "$30.00"

### Card 5: "Estado"
- Mostrar "Activo" o "Inactivo"
- Color verde si activo, rojo si inactivo

---

## 🗂️ Paso 7: Verificar Tab de Nodos

1. Haz click en el tab **"Nodos"** en la pestaña principal
2. Deberías ver una tabla con columnas:
   - **Nombre**: Nombre del nodo
   - **Serial**: Serial único (ej: SN-ABC-001)
   - **Estado**: Badge verde (online), rojo (offline), o gris (degraded)
   - **Última vez visto**: Fecha/hora de última conexión
   - **Ubicación**: Dirección o coordenadas
   - **IP WAN**: Dirección IP pública

### Verificaciones:
- [ ] La tabla muestra todos los nodos del tenant
- [ ] Los badges de estado tienen colores correctos
- [ ] Las fechas están formateadas correctamente (formato local)
- [ ] Las ubicaciones se muestran si existen
- [ ] Scroll horizontal funciona en móvil

---

## 📋 Paso 8: Verificar Tab de Tickets

1. Haz click en el tab **"Tickets"**
2. Deberías ver una tabla con columnas:
   - **Código**: Código único de 8 caracteres (ej: A3K9P2X7)
   - **Estado**: Badge de color (pending, active, expired, revoked)
   - **Plan**: Nombre del plan asociado
   - **Nodo**: Nombre del nodo
   - **Creado**: Fecha de creación
   - **Activado**: Fecha de activación (o "-")
   - **Expira**: Fecha de expiración (o "-")

### Verificaciones:
- [ ] Se muestran todos los tickets del tenant
- [ ] Estados tienen badges correctos
- [ ] Paginación funciona (botones Anterior/Siguiente)
- [ ] Contador muestra "Página X de Y (Total: N)"
- [ ] Máximo 100 tickets por página
- [ ] Scroll horizontal funciona en móvil

---

## 🔌 Paso 9: Verificar Tab de Sesiones

1. Haz click en el tab **"Sesiones"**
2. Deberías ver una tabla con columnas:
   - **MAC Dispositivo**: Dirección MAC del dispositivo
   - **IP**: Dirección IP del cliente
   - **Nodo**: Nodo conectado
   - **Iniciado**: Fecha/hora de inicio
   - **Expira**: Fecha/hora de expiración
   - **Estado**: Badge "Activa" (verde) o "Expirada" (gris)
   - **Bajada**: Datos descargados (ej: 150.25 MB)
   - **Subida**: Datos cargados (ej: 25.50 MB)

### Verificaciones:
- [ ] MACs están formateadas correctamente
- [ ] Bytes están convertidos a formato legible (B, KB, MB, GB)
- [ ] Estados tienen colores correctos
- [ ] Fechas están en formato local
- [ ] Scroll horizontal funciona en móvil

---

## 🎮 Paso 10: Testing de Acciones (Suspender/Activar)

### Crear un tenant de prueba:
1. En otra pestaña, navega a `/register`
2. Registra un nuevo usuario/tenant:
   - **Empresa**: "Test Suspend" + timestamp
   - **Email**: `test-suspend-{timestamp}@test.com`
   - **Password**: `testpass123`
3. Vuelve a la página de admin
4. Recarga la lista de tenants (F5 o cierra dropdown)
5. Busca el nuevo tenant en el dropdown

### Suspender el tenant:
1. Selecciona el nuevo tenant (si está en el dropdown)
2. Espera a que carguen las stats
3. En el card de "Estado", debería estar "Activo"
4. Busca un botón/opción de "Suspender" (esto requeriría agregar botones)

**Nota**: Actualmente no hay botones de suspender/activar en el UI. Requeriría API call manual:

```bash
curl -X PATCH http://localhost:8000/api/v1/admin/tenants/{tenant_id}/suspend \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🧪 Paso 11: Testing de Rendimiento

### Medir tiempos de carga:

**Con DevTools de Chrome**:
1. Abre DevTools (F12)
2. Tab "Network"
3. Selecciona un tenant
4. Observa los tiempos en las request:
   - GET `/admin/tenants/{id}/stats` → ~100-200ms
   - GET `/admin/tenants/{id}/nodes` → ~80-150ms
   - GET `/admin/tenants/{id}/tickets?skip=0&limit=100` → ~150-250ms
   - GET `/admin/tenants/{id}/sessions` → ~100-200ms

### Caché:
1. Selecciona un tenant
2. Espera a que carguen los datos
3. Cambia a otro tenant
4. Vuelve al primero → **Debería cargar instantáneamente desde caché**
5. Espera 30+ segundos → **Debería refrescar datos**

---

## 📱 Paso 12: Testing Responsivo

### En Desktop:
- [ ] 4 stat cards en una fila
- [ ] Tabs ocupan ancho completo
- [ ] Tablas tienen scroll horizontal si es necesario
- [ ] Fuentes legibles

### En Tablet (768px):
- [ ] 2 stat cards por fila
- [ ] Tabs se adaptan bien
- [ ] Tablas con scroll horizontal
- [ ] Touch-friendly

### En Mobile (375px):
- [ ] 1 stat card por fila
- [ ] Tabs apiladas o con scroll horizontal
- [ ] Tablas con scroll horizontal completo
- [ ] Botones grandes y fáciles de tocar
- [ ] Sin overflow horizontal innecesario

**Herramientas**:
```bash
# Chrome DevTools
- Ctrl+Shift+M (Windows) o Cmd+Shift+M (Mac)
- Selecciona dispositivos predefinidos
```

---

## 🌙 Paso 13: Testing Dark Mode

1. En el dashboard, busca el toggle de tema (usualmente en la esquina superior derecha)
2. Alterna entre light/dark mode
3. Verifica:
   - [ ] Colores se adaptan correctamente
   - [ ] Contraste es legible
   - [ ] Badges mantienen visibilidad
   - [ ] Tablas se ven bien en ambos modos

---

## 🔐 Paso 14: Testing de Seguridad (Permisos)

### Intentar acceder como operator:

```bash
# 1. Registra un operador
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Operator",
    "email": "operator@test.com",
    "password": "testpass123"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "operator@test.com",
    "password": "testpass123"
  }' | jq '.access_token'

# 3. Intenta acceder a /admin/overview (debería fallar con 403)
curl -H "Authorization: Bearer OPERATOR_TOKEN" \
  http://localhost:8000/api/v1/admin/overview
# Response: {"detail":"Forbidden"}
```

### En el UI:
1. Cierra sesión del superadmin
2. Registra/login con un operator
3. Navega a `/admin/tenants`
4. Debería mostrar error 403 o redirigir a home

---

## ✅ Checklist Final

### Backend:
- [ ] 8 endpoints funcionan correctamente
- [ ] Solo superadmin puede acceder (403 para otros)
- [ ] Respuestas tienen estructura correcta
- [ ] Paginación funciona
- [ ] Tiempos de respuesta < 300ms

### Frontend:
- [ ] Página carga en < 2 segundos
- [ ] Stats cards muestran datos correctos
- [ ] Dropdown de tenants funciona
- [ ] 3 tabs (Nodos, Tickets, Sesiones) funcionan
- [ ] Paginación de tickets funciona
- [ ] Responsive en desktop, tablet, mobile
- [ ] Dark mode funciona
- [ ] Skeleton loaders aparecen durante carga
- [ ] Mensajes de error "Sin datos" aparecen cuando corresponde

### Seguridad:
- [ ] Solo superadmin puede acceder
- [ ] Operators reciben 403
- [ ] No hay errores de XSS o injection

### Performance:
- [ ] React Query cachea datos correctamente
- [ ] Datos se refrescan después de 30-60 segundos
- [ ] Cambiar de tenant no causa refetch innecesarios
- [ ] Paginación no causa slowdown

---

## 🐛 Reportar Bugs

Si encuentras un problema:

1. **Describe el bug**:
   - Qué hiciste
   - Qué esperabas
   - Qué pasó en su lugar

2. **Información técnica**:
   - User-Agent del navegador
   - Screenshoot o video
   - Logs de la consola (F12)

3. **Crea un issue en GitHub**:
   ```
   https://github.com/adrpinto83/jadslink/issues
   ```

---

## 🎉 ¡Listo!

Si todos los pasos anteriores pasan exitosamente, el Panel de Gestión de Tenants está completamente funcional y listo para producción.

---

**Última actualización**: 2026-04-30
**Responsable**: JADS Studio
