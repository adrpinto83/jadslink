# JADSlink OpenWrt Configuration Guide

Guía completa para configurar un dispositivo TP-Link con OpenWrt como nodo JADSlink.

## 📋 Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Opción 1: Setup Wizard (Recomendado)](#opción-1-setup-wizard-recomendado)
3. [Opción 2: Manual paso a paso](#opción-2-manual-paso-a-paso)
4. [Verificación y Testing](#verificación-y-testing)
5. [Troubleshooting](#troubleshooting)

---

## Requisitos Previos

### En tu máquina local:
- [x] Servidor JADSlink corriendo (`docker compose up`)
- [x] Dashboard funcional (http://localhost:5173)
- [x] Python 3.9+
- [x] SSH client (`ssh` command available)
- [x] SCP client (`scp` command available)

### En OpenWrt:
- [x] OpenWrt 22.03+ instalado
- [x] SSH habilitado (System → System → Enable SSH Server)
- [x] Conectado a la red (WAN hacia internet)
- [x] Acceso root via SSH

### En el Dashboard:
- [x] Nodo creado (Nodos → Crear Nodo)
- [x] Planes creados (Planes → Crear)
- [x] Tickets generados (Tickets → Generar)

---

## Opción 1: Setup Wizard (Recomendado)

### Paso 1: Prepara las Credenciales

Antes de ejecutar el wizard, asegúrate de tener listas:
1. La IP de tu OpenWrt (ej: `10.0.0.1` o `192.168.0.209`)
2. El usuario SSH (normalmente `root`)
3. Las credenciales del nodo del dashboard:
   - `NODE_ID` (UUID)
   - `API_KEY` (sk_live_...)
   - `SERVER_URL` (http://192.168.0.X:8000)

### Paso 2: Ejecuta el Wizard

```bash
cd /home/adrpinto/jadslink/agent
python3 setup-wizard.py
```

El wizard te guiará a través de:
1. ✓ Validación del setup local
2. ✓ Conexión a OpenWrt vía SSH
3. ✓ Recolección de credenciales
4. ✓ Despliegue del agente
5. ✓ Inicio del servicio

**Tiempo estimado: 5-10 minutos**

### Paso 3: Verifica en Dashboard

1. Ve a **Dashboard → Nodos**
2. Tu nodo debe aparecer con estado **"online"** (verde)
3. Verifica métricas en tiempo real

---

## Opción 2: Manual paso a paso

### 2.1 Validar Setup Local

```bash
cd /home/adrpinto/jadslink/agent
python3 validate-setup.py
```

**Debe pasar todas las validaciones** antes de continuar.

### 2.2 Preparar Credenciales OpenWrt

```bash
# Obtén estas del dashboard
# Dashboard → Nodos → [Tu Nodo]
export NODE_ID="33bdb4bd-7516-4bdd-9133-a1b4743a0a8d"
export API_KEY="sk_live_1B716280474F323FA05C79..."
export SERVER_URL="http://192.168.0.X:8000"
export OPENWRT_IP="10.0.0.1"
```

### 2.3 Conectar a OpenWrt vía SSH

```bash
ssh root@$OPENWRT_IP
# Te pedirá password
```

### 2.4 Ejecutar Setup en OpenWrt

Una vez dentro de OpenWrt:

```bash
# Crear directorio temporal
mkdir -p /tmp/jadslink-setup
cd /tmp/jadslink-setup

# Descargar script de setup
# (O transferir manualmente con SCP)
```

**Alternativa: Transferir script desde tu máquina local:**

```bash
# En tu máquina local
scp -P 22 /home/adrpinto/jadslink/agent/openwrt-setup.sh root@$OPENWRT_IP:/tmp/
```

**Luego en OpenWrt:**

```bash
bash /tmp/openwrt-setup.sh
# Te pedirá las credenciales durante la ejecución
```

### 2.5 Transferir Archivos del Agente

```bash
# En tu máquina local
cd /home/adrpinto/jadslink/agent
bash deploy-to-openwrt.sh $OPENWRT_IP
```

### 2.6 Verificar Instalación

```bash
# Desde tu máquina local
bash test-openwrt.sh $OPENWRT_IP
```

### 2.7 Iniciar Agente

```bash
# En OpenWrt vía SSH
ssh root@$OPENWRT_IP '/etc/init.d/jadslink start'
```

---

## Verificación y Testing

### Test 1: Nodo Online en Dashboard

1. Ve a **Dashboard → Nodos**
2. Tu nodo debe aparecer **"online"** (dentro de 30 segundos)
3. Ver último heartbeat y métricas

### Test 2: WiFi Abierto Funcional

**Desde un móvil:**

1. Escanea redes WiFi
2. Busca **"JADSlink-WiFi"** (sin contraseña)
3. Conecta

### Test 3: Portal Captive

**Desde el móvil conectado:**

1. Abre navegador
2. Intenta ir a cualquier sitio (ej: google.com)
3. Deberías ser **redirigido automáticamente** al portal
4. Ver formulario con campo "Código de Ticket"

**Si no ves el portal:**
```bash
# Ver logs del agente
ssh root@10.0.0.1 'logread | grep portal'

# Verificar puerto 80
ssh root@10.0.0.1 'netstat -tlnp | grep :80'
```

### Test 4: Activar Ticket

**En el portal captive:**

1. Obtén un código de ticket del dashboard
2. Ingresa código (ej: "5YIR5A24")
3. Click "Activar"
4. Ver confirmación: "✓ Ticket Activado"

### Test 5: Acceso a Internet

**Desde el móvil:**

1. Después de activar ticket
2. Intenta acceder a un sitio web (google.com, etc)
3. **Debe funcionar sin problemas**

### Test 6: Sesión en Dashboard

**En tu máquina:**

1. Ve a **Dashboard → Sesiones**
2. Ver sesión activa con:
   - Código del ticket
   - MAC del dispositivo
   - Tiempo restante
   - Nodo

### Test 7: Expiración Automática

**Espera a que expire el ticket:**

1. Si es plan de 30 minutos, espera 30 min
2. O edita el plan para test rápido (5 minutos)
3. Después de expirar:
   - El móvil pierde acceso
   - Sesión cambia a "expired"
   - Volver a redirigir a portal

---

## Comandos Útiles

### Ver estado del agente

```bash
ssh root@10.0.0.1 'ps | grep agent.py'
```

### Ver logs en tiempo real

```bash
ssh root@10.0.0.1 'logread -f | grep jadslink'
```

### Reiniciar agente

```bash
ssh root@10.0.0.1 '/etc/init.d/jadslink restart'
```

### Ver configuración

```bash
ssh root@10.0.0.1 'cat /opt/jadslink/.env'
```

### Ver reglas iptables

```bash
ssh root@10.0.0.1 'iptables -t filter -L JADSLINK_FORWARD -n -v'
ssh root@10.0.0.1 'iptables -t nat -L JADSLINK_PREROUTING -n -v'
```

### Ver sesiones SQLite

```bash
ssh root@10.0.0.1 'sqlite3 /opt/jadslink/.cache/tickets.db "SELECT * FROM sessions;"'
```

### Detener agente

```bash
ssh root@10.0.0.1 '/etc/init.d/jadslink stop'
```

### Borrar cache local

```bash
ssh root@10.0.0.1 'rm -rf /opt/jadslink/.cache/*'
```

---

## Troubleshooting

### ❌ "No se puede conectar a OpenWrt"

**Solución:**
```bash
# 1. Verificar que OpenWrt está encendido
ping 10.0.0.1

# 2. Habilitar SSH en LuCI
# http://10.0.0.1
# System → System → Enable SSH

# 3. Verificar puerto SSH
ssh -v root@10.0.0.1

# 4. Reiniciar OpenWrt
ssh root@10.0.0.1 'reboot'
```

### ❌ "Nodo no aparece online"

**Solución:**
```bash
# 1. Verificar que agente está corriendo
ssh root@10.0.0.1 'ps | grep agent.py'

# 2. Ver logs de error
ssh root@10.0.0.1 'logread | grep -i error'

# 3. Verificar .env
ssh root@10.0.0.1 'cat /opt/jadslink/.env'

# 4. Verificar conectividad al servidor
ssh root@10.0.0.1 'curl http://SERVER_URL/docs'

# 5. Reiniciar agente
ssh root@10.0.0.1 '/etc/init.d/jadslink restart'
```

### ❌ "Portal no redirige a 80"

**Solución:**
```bash
# 1. Verificar iptables DNAT
ssh root@10.0.0.1 'iptables -t nat -L JADSLINK_PREROUTING -n -v'

# Debe mostrar:
# DNAT tcp dpt:80 to:10.0.0.1:80

# 2. Si no existe, crear manualmente
ssh root@10.0.0.1 'iptables -t nat -N JADSLINK_PREROUTING'
ssh root@10.0.0.1 'iptables -t nat -A JADSLINK_PREROUTING -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:80'
ssh root@10.0.0.1 'iptables -t nat -A PREROUTING -j JADSLINK_PREROUTING'

# 3. Guardar reglas
ssh root@10.0.0.1 'sh /etc/firewall.user'
```

### ❌ "Ticket no se activa"

**Solución:**
```bash
# 1. Verificar código en base de datos
ssh root@10.0.0.1 'sqlite3 /opt/jadslink/.cache/tickets.db "SELECT code, status FROM tickets LIMIT 10;"'

# 2. Si no hay tickets, sincronizar
ssh root@10.0.0.1 'cd /opt/jadslink && python3 -c "from sync import ServerSync; from config import AgentConfig; from cache import TicketCache; sync=ServerSync(AgentConfig(), TicketCache()); sync.sync_tickets()"'

# 3. Ver logs
ssh root@10.0.0.1 'logread | grep -i ticket'

# 4. Reiniciar agente
ssh root@10.0.0.1 '/etc/init.d/jadslink restart'
```

### ❌ "Cliente no obtiene internet tras activar"

**Solución:**
```bash
# 1. Obtener MAC del cliente
ssh root@10.0.0.1 'arp -n'

# 2. Verificar regla en iptables
ssh root@10.0.0.1 'iptables -t filter -L JADSLINK_FORWARD -n -v'

# 3. Verificar forwarding IP está habilitado
ssh root@10.0.0.1 'sysctl net.ipv4.ip_forward'
# Debe ser: net.ipv4.ip_forward = 1

# 4. Verificar NAT en WAN
ssh root@10.0.0.1 'iptables -t nat -L POSTROUTING -n -v'
```

### ❌ "Alto consumo de RAM/CPU"

**Solución:**
```bash
# 1. Ver consumo del agente
ssh root@10.0.0.1 'ps aux | grep agent'

# 2. Revisar logs de error
ssh root@10.0.0.1 'logread | tail -50'

# 3. Limpiar cache
ssh root@10.0.0.1 'rm -rf /opt/jadslink/.cache/tickets.db'

# 4. Reiniciar agente
ssh root@10.0.0.1 '/etc/init.d/jadslink restart'
```

---

## Archivos Generados

Después del setup, tu OpenWrt tendrá:

```
/opt/jadslink/
├── agent.py              # Loop principal del agente
├── config.py             # Lectura de configuración
├── firewall.py           # Gestión de iptables
├── portal.py             # HTTP server (80)
├── session_manager.py    # Activación de sesiones
├── sync.py               # Comunicación con servidor
├── cache.py              # SQLite local
├── .env                  # Configuración (NODE_ID, API_KEY, etc)
├── .cache/
│   ├── tickets.db        # Base de datos local
│   └── portal.html       # Portal HTML cacheado
└── firewall.user         # Reglas iptables persistentes

/etc/init.d/jadslink      # Service init script
/etc/config/network       # Configuración de red (UCI)
/etc/config/wireless      # Configuración WiFi (UCI)
/etc/config/dhcp          # Configuración DHCP (UCI)
```

---

## Siguientes Pasos

### 1. Generar más tickets
```
Dashboard → Tickets → Generar Batch
Selecciona nodo, plan y cantidad
Descarga PDF con QR codes
```

### 2. Imprimir y distribuir
```
Imprime el PDF con QR codes
Distribuye físicamente o por WhatsApp
```

### 3. Monitorear uso
```
Dashboard → Sessions (sesiones activas)
Dashboard → Reports (estadísticas)
```

### 4. Escalar a más nodos
```
Repite el mismo proceso para cada dispositivo TP-Link
Cada uno con su propio NODE_ID y API_KEY
```

---

## Contacto y Soporte

**Documentación completa**: `/home/adrpinto/jadslink/CLAUDE.md`

**Logs**:
- En OpenWrt: `logread -f | grep jadslink`
- En servidor: `docker compose logs api`

**Issues**:
- GitHub: https://github.com/adrpinto83/jadslink/issues
- Email: support@jadslink.io

---

**Versión**: 1.0.0
**Última actualización**: 2026-04-25
**Estado**: Production Ready ✅
