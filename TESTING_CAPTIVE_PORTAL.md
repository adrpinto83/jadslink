# Testing del Portal Cautivo JADSlink

## Estado Actual del Sistema

✅ **Todo Configurado y Funcional**

### Componentes Activos:

1. **Router OpenWrt (192.168.1.1)**
   - SSID: `JADSLink` (ambas bandas 5GHz y 2.4GHz)
   - Modo: Abierto (sin contraseña)
   - Agente: Corriendo, enviando heartbeat cada 30s

2. **Portal Cautivo**
   - URL: http://192.168.1.1/portal/
   - Acceso: Automático (redirección transparente)
   - Autenticación: Cookie-based

3. **Backend API**
   - URL: http://localhost:8000
   - Heartbeat: Activo ✓
   - Sessions: Funcional ✓
   - Geolocation: Funcional con retry logic ✓

## Instrucciones de Testing

### 1️⃣ Verificar el Backend Está en Línea

```bash
# En tu máquina local
curl http://localhost:8000/docs

# Debería mostrar Swagger UI
```

✅ **Esperado**: Swagger UI cargue sin errores

---

### 2️⃣ Obtener un Código de Ticket

```bash
# Generar 5 tickets
curl -X POST http://localhost:8000/api/v1/plans \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "30 Minutos",
    "duration_minutes": 30,
    "price_usd": "2.50"
  }'

# O via dashboard
# Dashboard → Planes → Crear Plan → Generar Tickets
```

✅ **Esperado**: Obtener códigos como `A3K9P2X7`, `B2L5K9M3`, etc.

---

### 3️⃣ Conectarse a la WiFi JADSLink

**Desde tu dispositivo (teléfono/laptop)**:

1. Abrir ajustes WiFi
2. Buscar red: **JADSLink**
3. Conectar (sin contraseña)
4. Asignar IP: 192.168.1.100-249 automáticamente

```bash
# Verificar conexión
ping 192.168.1.1

# Debería responder
```

✅ **Esperado**: Conexión WiFi exitosa

---

### 4️⃣ Abrir Navegador y Verificar Redirección Automática

**Desde el dispositivo conectado**:

1. Abrir navegador (Chrome, Safari, Firefox)
2. Ir a cualquier URL: `http://google.com` o `http://bbc.com`
3. **Debería redirigir automáticamente** a `http://192.168.1.1/portal/`

```javascript
// En la consola del navegador, deberías ver:
// Redirigiendo desde http://google.com/... → http://192.168.1.1/portal/
```

✅ **Esperado**: Redirección automática sin acciones del usuario

---

### 5️⃣ Activar Ticket en el Portal

**En el portal que abrió automáticamente**:

1. **Página 1 - Seleccionar Plan**
   - La página carga planes disponibles
   - Haz click en un plan (ej: "30 Minutos - $2.50")
   - El plan se marca como seleccionado

2. **Página 2 - Ingresar Código**
   - Campo: "Código de acceso"
   - Ingresa un código que generaste (ej: `A3K9P2X7`)
   - Button "Activar Acceso" se habilitará

3. **Click en "Activar Acceso"**
   - La solicitud se envía al backend
   - Backend busca el ticket
   - Backend crea una sesión activa
   - Portal establece cookie `jadslink_authenticated=true`

✅ **Esperado**: Pantalla de éxito "✅ ¡Acceso Activado!"

---

### 6️⃣ Verificar Autenticación y Navegación Normal

**Después de activar**:

1. El portal debería mostrar:
   ```
   ✅ ¡Acceso Activado!
   Duración: 30 minutos
   ```

2. Auto-redirección a home (`/`) en 3 segundos

3. **Navegación Normal**:
   - Intenta acceder a http://google.com
   - Debería cargar normalmente (ya no redirigir)
   - La cookie sigue siendo válida

4. **Verifica la Cookie en el Navegador**:
   ```javascript
   // Abre console (F12) y ejecuta:
   document.cookie
   // Debería mostrar: "jadslink_authenticated=true"
   ```

✅ **Esperado**: Navegación normal sin redirecciones

---

### 7️⃣ Verificar Expiración de Cookie

**Esperar a que expire el plan** (si es de 30 minutos, esperar 30 min):

1. Tras expiración, la cookie se borra automáticamente
2. Intenta acceder a cualquier sitio
3. Debería redirigir nuevamente a portal

```javascript
// Verificar expiración:
console.log(document.cookie)
// La cookie debe desaparecer después del tiempo
```

✅ **Esperado**: Cookie desaparece automáticamente

---

### 8️⃣ Testear con Múltiples Dispositivos (Opcional)

Conecta 2-3 dispositivos simultáneamente:

- Dispositivo A: Sin autenticar → debe ver portal
- Dispositivo B: Autenticado → debe navegar normalmente
- Dispositivo C: Cookie expirada → debe ver portal de nuevo

✅ **Esperado**: Cada dispositivo tiene su propia cookie

---

## Dashboard - Verificar Sesiones Activas

**En http://localhost:5173/dashboard/**:

1. Ir a **Sessions** (Sesiones)
2. Deberías ver:
   - 1 sesión activa por cada usuario autenticado
   - IP del cliente
   - Hora de expiración
   - Duración

3. Ir a **Nodes**
   - El nodo debe mostrar estado "online"
   - Heartbeat debe ser reciente

✅ **Esperado**: Sesiones listadas con información correcta

---

## Troubleshooting

### 📍 Problema: No redirige automáticamente al portal

**Causas posibles**:
1. DNS spoofing no funciona
2. Firewall rules no están aplicadas

**Soluciones**:

```bash
# En el router:
ssh root@192.168.1.1

# Verificar dnsmasq
ps | grep dnsmasq
/etc/init.d/dnsmasq restart

# Verificar firewall
uci show firewall | grep "Captive Portal"
/etc/init.d/firewall restart

# Probar localmente
wget -q -O - http://127.0.0.1/portal/ | head -10
```

---

### 📍 Problema: Portal carga pero dice "Cargando planes..."

**Causas posibles**:
1. Backend no es accesible desde router
2. Endpoint `/api/v1/portal/plans` no existe

**Soluciones**:

```bash
# En el router:
ssh root@192.168.1.1

# Verificar conectividad al backend
wget -q -O - http://localhost:8000/docs | head -20

# Ver logs del agente
tail -50 /tmp/jadslink-agent.log

# En tu máquina (si el router está en otra red):
# Asegúrate que el puerto 8000 sea accesible desde 192.168.1.1
```

---

### 📍 Problema: Código dice "Error: Código inválido"

**Causas posibles**:
1. El código no existe en la BD
2. El código ya fue usado/expirado
3. El código es para otro nodo

**Soluciones**:

```bash
# Generar nuevos tickets en el dashboard
# O vía API:
curl -X POST http://localhost:8000/api/v1/tickets/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "YOUR_PLAN_ID",
    "count": 5,
    "node_id": "643f04f4-5244-4449-97fd-3c78cc13377c"
  }'
```

---

### 📍 Problema: Portal carga pero es el index.html del OpenWrt (LuCI)

**Causa**: Las redirecciones no están funcionando correctamente

**Solución**:

```bash
# En el router, verificar que /www/portal/index.html existe
ssh root@192.168.1.1
ls -la /www/portal/

# Si no existe, copiar manualmente:
# (Ya debería estar copiad, pero por si acaso)
```

---

## Logs Útiles para Debugging

### Backend (tu máquina)
```bash
# Terminal donde está corriendo FastAPI
# Deberías ver requests de:
# GET /api/v1/portal/plans?node_id=...
# POST /api/v1/portal/activate
```

### Router Agent
```bash
ssh root@192.168.1.1
tail -f /tmp/jadslink-agent.log

# Debería mostrar heartbeats exitosos
```

### dnsmasq
```bash
ssh root@192.168.1.1
tail -f /var/log/dnsmasq.log

# Debería mostrar resolved queries
```

### Firewall
```bash
ssh root@192.168.1.1
logread | grep -i firewall | tail -20
```

---

## Checklist Final

- [ ] Backend API corriendo en localhost:8000
- [ ] Router OpenWrt en línea con SSID "JADSLink"
- [ ] Agente bash enviando heartbeat (check logs)
- [ ] Tickets generados en el dashboard
- [ ] Página /www/portal/index.html existe en router
- [ ] Firewall rules configuradas (nftables)
- [ ] dnsmasq configurado para spoofing
- [ ] Dispositivo se conecta a WiFi
- [ ] Redirige automáticamente al portal
- [ ] Portal carga planes correctamente
- [ ] Ingresa código y activa acceso
- [ ] Cookie se establece
- [ ] Puede navegar normalmente
- [ ] Dashboard muestra sesión activa

---

## Próximos Pasos (si todo funciona)

1. **Testear en producción**: Replicar en múltiples routers
2. **Integrar with Stripe**: Pagos automáticos
3. **Mejorar UI**: Tema personalizable por tenant
4. **Analytics**: Dashboard de uso y ingresos
5. **Mobile App**: Aplicación nativa para activación

---

**Última actualización**: 2026-04-26
**Status**: Listo para testing ✅
