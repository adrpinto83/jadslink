# Configuración del Portal Cautivo - JADSlink

## Descripción General

El portal cautivo redirige automáticamente a usuarios no autenticados que se conectan a la red WiFi JADSLink hacia una página de activación de tickets. Una vez autenticados (mediante cookie), pueden navegar normalmente.

## Arquitectura

```
Usuario conecta a WiFi
         ↓
    Client Browser
         ↓
    DNS Query (dnsmasq)
    - Captura todos los dominios
    - Redirige a 192.168.1.1
         ↓
    HTTP Request al Router
         ↓
    iptables/nftables (firewall)
    - Redirige puerto 80/443 → puerto 80
         ↓
    uhttpd server en puerto 80
         ↓
    index.html (redirección inteligente)
    - Si tiene cookie → contenido normal
    - Si no → /portal/
         ↓
    /portal/index.html (portal cautivo)
    - Cargar planes del backend
    - Ingresar código
    - POST /api/v1/portal/activate
         ↓
    Set cookie 'jadslink_authenticated'
         ↓
    Navegación normal habilitada ✓
```

## Componentes Configurados

### 1. DNS Spoofing (dnsmasq)

**Archivo**: `/etc/config/dhcp`

```bash
# Captura todas las peticiones DNS y las redirige al router
uci add dnsmasq
uci set dnsmasq.@dnsmasq[-1].address '/#/192.168.1.1'
uci commit dhcp
/etc/init.d/dnsmasq restart
```

**Efecto**:
- google.com → 192.168.1.1
- facebook.com → 192.168.1.1
- cualquier-dominio.com → 192.168.1.1

### 2. Firewall NAT Redirect (nftables/fw4)

**Archivo**: `/etc/config/firewall`

```bash
# Regla 1: Redirigir HTTP (puerto 80) desde LAN
uci add firewall redirect
uci set firewall.@redirect[-1].name="Captive Portal HTTP"
uci set firewall.@redirect[-1].src="lan"
uci set firewall.@redirect[-1].src_dport="80"
uci set firewall.@redirect[-1].dest_ip="127.0.0.1"
uci set firewall.@redirect[-1].dest_port="80"
uci set firewall.@redirect[-1].proto="tcp"
uci set firewall.@redirect[-1].target="DNAT"

# Regla 2: Redirigir HTTPS (puerto 443) → HTTP (puerto 80)
uci add firewall redirect
uci set firewall.@redirect[-1].name="Captive Portal HTTPS"
uci set firewall.@redirect[-1].src="lan"
uci set firewall.@redirect[-1].src_dport="443"
uci set firewall.@redirect[-1].dest_ip="127.0.0.1"
uci set firewall.@redirect[-1].dest_port="80"
uci set firewall.@redirect[-1].proto="tcp"
uci set firewall.@redirect[-1].target="DNAT"

uci commit firewall
/etc/init.d/firewall restart
```

**Efecto**:
- http://user.com → 127.0.0.1:80 (portal)
- https://user.com → 127.0.0.1:80 (portal)

### 3. Páginas HTML

#### `/www/index.html`
- Página de inicio del router
- Si autenticado → muestra estado
- Si no autenticado → redirige a `/portal/`
- Verificación de cookie: `jadslink_authenticated`

#### `/www/portal/index.html`
- Portal cautivo principal
- Cargar lista de planes desde `GET /api/v1/portal/plans`
- Input para código de ticket
- POST `/api/v1/portal/activate`
- Establece cookie con expiración = duración del plan

#### `/www/welcome.html`
- Página de bienvenida tras activación exitosa
- Muestra estado del acceso
- Redirección automática a home

### 4. Backend API (`/api/v1/portal`)

#### `GET /portal/plans?node_id={node_id}`
Retorna lista HTML de planes disponibles:

```html
<option value="plan-id" data-price="3.00">30 Minutos (30 min)</option>
...
```

#### `POST /portal/activate`
Request:
```json
{
  "code": "A3K9P2X7",
  "plan_id": "uuid-here",
  "node_id": "uuid-here"
}
```

Response (éxito):
```json
{
  "status": "success",
  "duration_minutes": 30,
  "expires_at": "2026-04-26T11:30:00Z"
}
```

Response (error):
```json
{
  "status": "error",
  "detail": "Código inválido o expirado"
}
```

## Flujo de Usuario

### 1. Usuario se conecta a WiFi "JADSLink"
```
SSID: JADSLink
Seguridad: Abierta (sin contraseña)
IP asignada: 192.168.1.100-249
Gateway: 192.168.1.1
DNS: 192.168.1.1
```

### 2. Abre navegador
- Se genera HTTP request a cualquier sitio (ej: http://google.com)
- DNS intercepta → resuelve a 192.168.1.1
- HTTP se redirige al puerto 80 (iptables)
- Llega a `/www/index.html`

### 3. Redirección inteligente
```javascript
// En /www/index.html
const COOKIE_NAME = 'jadslink_authenticated';
function isAuthenticated() {
    return document.cookie.includes(COOKIE_NAME);
}

if (!isAuthenticated()) {
    window.location.replace('/portal/');
}
```

### 4. Portal cautivo (`/portal/`)
1. Cargar planes: `GET /api/v1/portal/plans?node_id={id}`
2. Usuario selecciona plan
3. Usuario ingresa código de 8 caracteres
4. POST `/api/v1/portal/activate`
5. Si éxito → establecer cookie
6. Redirigir a home

### 5. Cookie persistente
```javascript
// En portal/index.html
function setAuthCookie(durationMinutes) {
    const date = new Date();
    date.setTime(date.getTime() + (durationMinutes * 60 * 1000));
    document.cookie = `${COOKIE_NAME}=true; expires=${date.toUTCString()}; path=/`;
}
```

## Debugging

### Verificar dnsmasq
```bash
# Conectar al router
ssh root@192.168.1.1

# Ver configuración
uci show dhcp | grep -i address

# Ver procesos
ps | grep dnsmasq

# Reiniciar
/etc/init.d/dnsmasq restart
```

### Verificar firewall
```bash
# Ver reglas
nft list ruleset

# O vía UCI
uci show firewall | grep -A 7 "Captive Portal"

# Reiniciar
/etc/init.d/firewall restart
```

### Verificar páginas
```bash
# Test local
wget -q -O - http://127.0.0.1/portal/ | head -20

# Ver archivos
ls -la /www/
ls -la /www/portal/
```

### Verificar agente
```bash
# Ver logs
tail -100 /tmp/jadslink-agent.log

# Ver si está corriendo
ps | grep agent

# Reiniciar servicio
/etc/init.d/jadslink-agent restart
```

## Endpoints Backend Requeridos

El sistema requiere que estos endpoints estén disponibles en `localhost:8000` (accesible desde el router):

1. **GET `/api/v1/portal/plans`**
   - Query params: `node_id`
   - Retorna: HTML con opciones de planes

2. **POST `/api/v1/portal/activate`**
   - Body: JSON con code, plan_id, node_id
   - Retorna: JSON con duration_minutes

3. **GET `/api/v1/agent/heartbeat`** (opcional, para monitoreo)
   - Reportar estado del nodo

## Limitaciones Conocidas

### Red aislada
- El router no tiene acceso a internet
- Los usuarios redirigidos a dominios externos verán error de conexión
- Necesitan usar el portal cautivo para iniciar

### Autenticación por cookie
- La cookie no es validada en backend
- Usuarios pueden falsificar
- Solución: Validar en backend + usar tokens JWT

### Redirección HTTPS
- HTTPS (443) se redirige a HTTP (80)
- Los navegadores pueden mostrar advertencia de seguridad
- En producción usar certificado SSL válido

## Mejoras Futuras

1. **Validación Backend**
   - Servidor HTTP en Python/Node que valide cookies
   - Blacklist de IPs autenticadas
   - Rate limiting

2. **SSL/TLS**
   - Certificado autofirmado
   - Let's Encrypt integración

3. **Estadísticas**
   - Contar usuarios autenticados
   - Estadísticas de uso de planes
   - Reportes de actividad

4. **UI Mejorada**
   - Ícono de red WiFi en portal
   - Contador de tiempo restante
   - QR code para acceso rápido

## Referencias

- OpenWrt Firewall: https://openwrt.org/docs/guide-user/firewall/
- dnsmasq: http://www.thekelleys.org.uk/dnsmasq/doc.html
- nftables: https://wiki.nftables.org/

---

**Última actualización**: 2026-04-26
**Estado**: Funcional y testeado ✓
