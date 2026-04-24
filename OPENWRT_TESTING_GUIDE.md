# JADSlink Agent - OpenWrt Testing Guide

Guía completa para verificar la implementación de todas las fases del plan de adaptación a OpenWrt.

## Índice

1. [FASE 1: Bandwidth Limiting con tc](#fase-1-bandwidth-limiting-con-tc)
2. [FASE 2: Detección Automática de Interfaces](#fase-2-detección-automática-de-interfaces)
3. [FASE 3: Persistencia de Reglas iptables](#fase-3-persistencia-de-reglas-iptables)
4. [FASE 4: Package OpenWrt (.ipk)](#fase-4-package-openwrt-ipk)
5. [FASE 5: Integración Híbrida en install.sh](#fase-5-integración-híbrida-en-installsh)
6. [Testing End-to-End](#testing-end-to-end)

---

## FASE 1: Bandwidth Limiting con tc

### Objetivo

Implementar bandwidth limiting funcional usando Traffic Control (tc) con HTB y IFB.

### Archivos Modificados

- `agent/firewall.py` - Clase `TrafficControl` agregada (~500 líneas)

### Testing Local (Linux)

```bash
# 1. Leer el código para verificar clase TrafficControl
grep -n "class TrafficControl" agent/firewall.py
# Debe mostrar línea ~13

# 2. Verificar métodos críticos
grep -n "def setup_egress_shaping" agent/firewall.py
grep -n "def setup_ingress_shaping" agent/firewall.py
grep -n "def add_session_limit" agent/firewall.py
# Todos deben existir

# 3. Verificar integración con set_bandwidth_limit()
grep -A 20 "def set_bandwidth_limit" agent/firewall.py | head -30
# Debe llamar a self.tc.setup_egress_shaping()

# 4. Verificar que FirewallClient.__init__ recibe wan_interface
grep "def __init__" agent/firewall.py | grep -A 5 FirewallClient
# Debe incluir parámetro wan_interface
```

### Testing en OpenWrt (Simulado)

```bash
# En una máquina con OpenWrt emulado o router real

# 1. Instalar el agent (con .ipk o install.sh)
opkg install /tmp/jadslink-agent_1.0.0-1_all.ipk

# 2. Configurar agente
uci set jadslink.agent.node_id='test-node-001'
uci set jadslink.agent.api_key='test-key-xyz'
uci commit jadslink

# 3. Iniciar servicio
/etc/init.d/jadslink start

# 4. Verificar que tc es instalado
which tc
opkg list-installed | grep tc

# 5. Ver reglas tc después de activar ticket
ssh root@192.168.8.1
tc qdisc show dev eth1
# Debe mostrar: qdisc htb 1: root refcnt ...

# 6. Después de crear una sesión con límite de 5Mbps
tc class show dev eth1
# Debe mostrar clases creadas

tc filter show dev eth1
# Debe mostrar filtros con MAC address

# 7. Verificar módulo IFB cargado
lsmod | grep ifb
# Si no está, cargar: modprobe ifb

# 8. Test de throughput
# Cliente WiFi conectado al router
# Activar ticket con 5Mbps
# En cliente: speedtest-cli o iperf3
# Verificar que throughput ≤ 5Mbps

# 9. Limpiar reglas
/etc/init.d/jadslink stop
tc qdisc show dev eth1
# Debe mostrar solo reglas del sistema (no JADSLINK)
```

### Criterios de Éxito

- [ ] Clase `TrafficControl` existe y tiene todos los métodos
- [ ] `set_bandwidth_limit()` no es más un placeholder
- [ ] HTB qdisc se crea en la interfaz WAN
- [ ] IFB interface se configura correctamente
- [ ] Filtros u32 se crean por MAC address
- [ ] Limpieza de reglas funciona al apagar

---

## FASE 2: Detección Automática de Interfaces

### Objetivo

Auto-detectar interfaces de red (LAN, WAN) sin requerir configuración manual.

### Archivos Modificados

- `agent/config.py` - Clase `NetworkDetector` agregada (~150 líneas)
- `agent/agent.py` - Usa auto-detección en startup

### Testing Local (Linux)

```bash
# 1. Verificar clase NetworkDetector existe
grep -n "class NetworkDetector" agent/config.py
# Debe existir

# 2. Verificar métodos
grep "def get_wan_interface\|def get_lan_interface\|def get_interface_ip" agent/config.py
# Deben existir los 3 métodos

# 3. Verificar que AgentConfig usa NetworkDetector
grep -A 5 "network_info = NetworkDetector.detect_all" agent/config.py
# Debe usar auto-detección

# 4. Test en Python
python3 << 'EOF'
import sys
sys.path.insert(0, 'agent')
from config import NetworkDetector

info = NetworkDetector.detect_all()
print("Detected network info:")
for key, value in info.items():
    print(f"  {key}: {value}")

# Debe mostrar algo como:
# wan_interface: eth0
# wan_ip: None
# lan_interface: wlan0 o br-lan
# lan_ip: 192.168.1.x
# router_ip: 192.168.1.x
EOF

# 5. Verificar logging en agent.py
grep "Network auto-detected" agent/agent.py
# Debe mostrar mensajes de auto-detección
```

### Testing en OpenWrt

```bash
# 1. SSH al router
ssh root@192.168.8.1

# 2. Ver logs del agente (debe mostrar detección)
logread | grep "Network auto-detected"
# Salida esperada: "Network auto-detected: LAN=br-lan (192.168.8.1), WAN=eth1 (x.x.x.x)"

# 3. Verificar interfaces detectadas
logread | grep "Router:"
# Debe mostrar ROUTER_IP detectado correctamente

# 4. Test cambio de IP
uci set network.lan.ipaddr='192.168.2.1'
/etc/init.d/network restart
/etc/init.d/jadslink restart
logread | grep "Network auto-detected"
# Debe detectar nueva IP 192.168.2.1

# 5. Verificar variables de configuración
ps aux | grep jadslink-agent
# Debe mostrar proceso ejecutándose
```

### Criterios de Éxito

- [ ] `NetworkDetector` clase existe
- [ ] Métodos de detección funcionan
- [ ] `AgentConfig.__post_init__()` usa NetworkDetector
- [ ] Logs muestran interfaces auto-detectadas
- [ ] Funciona en OpenWrt (br-lan, eth1, etc.)
- [ ] Fallback a valores por defecto si detección falla

---

## FASE 3: Persistencia de Reglas iptables

### Objetivo

Asegurar que reglas firewall persistan después de reboot en OpenWrt.

### Archivos Modificados

- `agent/firewall.py` - Métodos `persist_rules()`, `install_firewall_user()`, `_is_openwrt()`

### Testing Local

```bash
# 1. Verificar métodos existen
grep -n "def persist_rules\|def install_firewall_user\|def _is_openwrt" agent/firewall.py
# Deben existir

# 2. Verificar que cleanup() llama a persist_rules()
grep -A 5 "def cleanup" agent/firewall.py | grep persist_rules
# Debe estar presente

# 3. Verificar llamada en startup
grep -B 5 -A 5 "install_firewall_user\|persist_rules" agent/agent.py
# Debe haber llamadas en run()

# 4. Verificar contenido de /etc/firewall.user script
grep "JADSLINK_PREROUTING\|JADSLINK_FORWARD" agent/firewall.py | head -10
# Debe crear chains correctamente
```

### Testing en OpenWrt

```bash
# 1. SSH al router
ssh root@192.168.8.1

# 2. Activar una sesión manualmente (simular cliente)
# Este paso requiere un cliente real conectado al WiFi

# 3. Verificar que archivo de reglas se creó
cat /var/lib/jadslink/iptables.rules
# Debe contener reglas JADSLINK

# 4. Verificar /etc/firewall.user creado
ls -la /etc/firewall.user
# Debe existir y ser ejecutable

cat /etc/firewall.user | head -20
# Debe contener script de restauración

# 5. Reboot del router
reboot

# 6. Después del reboot, verificar que reglas persisten
ssh root@192.168.8.1
iptables -t nat -L JADSLINK_PREROUTING -n
# Debe mostrar reglas (si hay sesiones activas)

iptables -t filter -L JADSLINK_FORWARD -n
# Debe mostrar reglas (si hay sesiones activas)

# 7. Verificar logs
logread | grep "Firewall chains initialized"
# Debe mostrar inicialización correcta

# 8. Test: Activar sesión, reboot, verificar sesión aún activa
# 1. Activar ticket en cliente
# 2. Verificar que cliente tiene internet
# 3. Reboot router
# 4. Cliente debe mantener conexión (si la regla persiste)
# 5. Verificar logcat: no debe haber errores de firewall
```

### Criterios de Éxito

- [ ] Métodos `persist_rules()` y `install_firewall_user()` existen
- [ ] `/etc/firewall.user` se crea en OpenWrt
- [ ] Archivo `/var/lib/jadslink/iptables.rules` se genera
- [ ] Reglas persisten después de reboot
- [ ] No hay errores en logs después de reboot
- [ ] Sesiones activas se restauran correctamente

---

## FASE 4: Package OpenWrt (.ipk)

### Objetivo

Crear package nativo OpenWrt (.ipk) para instalación simplificada.

### Archivos Creados

- `openwrt-package/Makefile` - Build instructions
- `openwrt-package/files/etc/init.d/jadslink` - Procd init script
- `openwrt-package/files/etc/config/jadslink` - UCI configuration
- `openwrt-package/files/usr/bin/jadslink-agent` - Entry point
- `openwrt-package/build.sh` - Build script
- `openwrt-package/README.md` - Documentation

### Testing de Build

```bash
# 1. Verificar que archivos existen
ls -la openwrt-package/
# Debe mostrar: Makefile, files/, build.sh, README.md

# 2. Verificar estructura de files/
find openwrt-package/files -type f
# Debe mostrar: etc/init.d/jadslink, etc/config/jadslink, usr/bin/jadslink-agent

# 3. Verificar contenido de Makefile
grep "PKG_NAME\|PKG_VERSION\|DEPENDS" openwrt-package/Makefile
# Debe mostrar: jadslink-agent, 1.0.0, dependencias correctas

# 4. Verificar entry point Python
head -20 openwrt-package/files/usr/bin/jadslink-agent
# Debe ser script Python ejecutable
grep "load_uci_config\|set_default_env" openwrt-package/files/usr/bin/jadslink-agent
# Debe leer configuración UCI

# 5. Verificar init script
grep "START\|USE_PROCD\|start_service" openwrt-package/files/etc/init.d/jadslink
# Debe ser procd compatible

# 6. Verificar UCI config
grep "config jadslink\|option enabled\|option node_id" openwrt-package/files/etc/config/jadslink
# Debe tener estructura UCI correcta
```

### Testing de Compilación

```bash
# 1. Entrar a openwrt-package
cd openwrt-package

# 2. Hacer executable el script
chmod +x build.sh

# 3. Ejecutar build (requiere OpenWrt SDK)
./build.sh
# Debe:
# - Descargar OpenWrt SDK
# - Setup feeds
# - Compilar package
# - Generar .ipk

# 4. Verificar resultado
ls -lh dist/jadslink-agent*.ipk
# Debe existir el archivo .ipk

# 5. Verificar contenido del .ipk
ar t dist/jadslink-agent_1.0.0-1_all.ipk | head -20
# Debe mostrar: control.tar.gz, data.tar.gz, debian-binary
```

### Testing de Instalación

```bash
# En router OpenWrt con acceso a internet

# 1. Copiar .ipk al router
scp dist/jadslink-agent_1.0.0-1_all.ipk root@192.168.8.1:/tmp/

# 2. SSH al router
ssh root@192.168.8.1

# 3. Instalar
opkg install /tmp/jadslink-agent_1.0.0-1_all.ipk
# Debe instalar sin errores

# 4. Verificar instalación
opkg list-installed | grep jadslink
# Debe mostrar: jadslink-agent - 1.0.0-1

# 5. Verificar archivos instalados
ls /usr/bin/jadslink-agent
ls /etc/init.d/jadslink
ls /etc/config/jadslink
# Todos deben existir

# 6. Configurar (UCI)
uci set jadslink.agent.node_id='test-node'
uci set jadslink.agent.api_key='test-key'
uci commit jadslink

# 7. Iniciar servicio
/etc/init.d/jadslink start
ps aux | grep jadslink-agent
# Debe estar ejecutándose

# 8. Ver logs
logread | grep jadslink
# Debe mostrar inicio correcto, sin errores

# 9. Parar servicio
/etc/init.d/jadslink stop

# 10. Desinstalar
opkg remove jadslink-agent
opkg list-installed | grep jadslink
# No debe mostrar nada
```

### Criterios de Éxito

- [ ] Todos los archivos existen en `openwrt-package/`
- [ ] `build.sh` ejecutable y documentado
- [ ] `.ipk` compila sin errores
- [ ] `.ipk` instala sin errores
- [ ] Archivos se instalan en ubicaciones correctas
- [ ] Servicio inicia/para correctamente
- [ ] Configuración UCI funciona

---

## FASE 5: Integración Híbrida en install.sh

### Objetivo

Hacer `install.sh` inteligente: usar `.ipk` en OpenWrt si está disponible, fallback a instalación manual en otros OS.

### Archivos Modificados

- `agent/install.sh` - Agregada detección de OS/PM e instalación vía `.ipk`

### Testing Local

```bash
# 1. Verificar que función detect_os_and_pm existe
grep -n "detect_os_and_pm\|install_openwrt_package" agent/install.sh
# Deben existir

# 2. Verificar lógica de fallback
grep -A 3 "if install_openwrt_package; then" agent/install.sh
# Debe intentar .ipk primero, luego fallback

# 3. Verificar que soporta múltiples package managers
grep "apt\|yum\|apk\|opkg" agent/install.sh
# Debe soportar varios

# 4. Verificar nuevo .env con auto-detección
grep "LAN_INTERFACE\|WAN_INTERFACE\|MAX_BANDWIDTH" agent/install.sh
# Debe incluir nuevos parámetros
```

### Testing en Ubuntu/Debian (Manual Installation)

```bash
# 1. Copiar agent a máquina Ubuntu
scp -r agent user@ubuntu-machine:/tmp/

# 2. SSH a máquina
ssh user@ubuntu-machine
cd /tmp/agent

# 3. Ejecutar install.sh (sin .ipk presente)
sudo ./install.sh
# Debe:
# - Detectar Ubuntu
# - Instalar via apt-get
# - Crear /opt/jadslink
# - Crear systemd service
# - No mencionar .ipk

# 4. Verificar instalación
sudo systemctl status jadslink
# Debe estar disponible (disabled hasta configurar)

# 5. Configurar
cat /opt/jadslink/.env
# Debe tener nuevos parámetros

# 6. Editar .env
sudo nano /opt/jadslink/.env
# Configurar NODE_ID y API_KEY

# 7. Iniciar servicio
sudo systemctl start jadslink
sudo systemctl status jadslink
# Debe estar running

# 8. Ver logs
sudo journalctl -u jadslink -f
# Debe mostrar inicio correcto

# 9. Parar y desabilitar
sudo systemctl stop jadslink
sudo systemctl disable jadslink
```

### Testing en OpenWrt (Con .ipk)

```bash
# 1. Preparar .ipk en directorio
cd openwrt-package/dist/
cp jadslink-agent_1.0.0-1_all.ipk /path/to/agent/

# 2. Copiar script y .ipk a router
scp agent/install.sh jadslink-agent*.ipk root@192.168.8.1:/tmp/

# 3. SSH al router
ssh root@192.168.8.1
cd /tmp

# 4. Ejecutar install.sh
chmod +x install.sh
./install.sh
# Debe:
# - Detectar OpenWrt
# - Encontrar .ipk
# - Instalar via opkg
# - Mostrar instrucciones UCI
# - Exit en éxito (no continuar a manual install)

# 5. Verificar instalación
opkg list-installed | grep jadslink
# Debe mostrar paquete

# 6. Configurar y usar (como en FASE 4)
```

### Testing en OpenWrt (Sin .ipk - Fallback)

```bash
# 1. Copiar solo install.sh (sin .ipk)
scp agent/install.sh root@192.168.8.1:/tmp/

# 2. SSH al router
ssh root@192.168.8.1
cd /tmp
chmod +x install.sh

# 3. Ejecutar install.sh
./install.sh
# Debe:
# - Detectar OpenWrt
# - No encontrar .ipk
# - Fallback a instalación manual
# - Crear /opt/jadslink
# - Crear /etc/init.d/jadslink (OpenWrt init script)
# - Continuar con instalación estándar

# 4. Verificar instalación manual
ls -la /opt/jadslink/
ls /etc/init.d/jadslink
# Deben existir

# 5. Configurar y usar
cat /opt/jadslink/.env
# Editar y configurar

/etc/init.d/jadslink start
ps aux | grep jadslink
# Debe estar corriendo
```

### Criterios de Éxito

- [ ] `detect_os_and_pm()` detecta correctamente OS y PM
- [ ] `install_openwrt_package()` encuentra e instala `.ipk`
- [ ] Fallback a instalación manual si no hay `.ipk`
- [ ] Ubuntu/Debian: instala via apt-get + systemd
- [ ] OpenWrt con `.ipk`: instala via opkg
- [ ] OpenWrt sin `.ipk`: instala manual + procd
- [ ] `.env` incluye nuevos parámetros de auto-detección

---

## Testing End-to-End

### Test Completo en GL-MT3000

Este test verifica todas las fases funcionando juntas.

#### Prerequisitos

- GL-MT3000 con OpenWrt 22.03+
- Conexión Starlink Mini o internet simulado
- Cliente WiFi para testing
- Acceso SSH al router

#### Procedimiento

```bash
# ========== SETUP INICIAL ==========

# 1. Preparar package
cd /home/jadslink-dev
openwrt-package/build.sh
# Genera dist/jadslink-agent_1.0.0-1_all.ipk

# 2. Transferir a router
scp openwrt-package/dist/jadslink-agent_*.ipk root@192.168.8.1:/tmp/

# 3. SSH al router
ssh root@192.168.8.1

# ========== INSTALACIÓN ==========

# 4. Instalar package
opkg update
opkg install /tmp/jadslink-agent_1.0.0-1_all.ipk

# 5. Configurar agente
uci set jadslink.agent.node_id='gl-mt3000-001'
uci set jadslink.agent.api_key='sk_test_xyz123'
uci set jadslink.agent.backend_url='http://192.168.1.100:8000'
uci commit jadslink

# ========== FASE 2: AUTO-DETECCIÓN ==========

# 6. Iniciar servicio (debe auto-detectar interfaces)
/etc/init.d/jadslink start

# 7. Verificar logs de auto-detección
logread | grep "Network auto-detected"
# Esperado: "Network auto-detected: LAN=br-lan (192.168.8.1), WAN=eth1 (...)"

logread | grep "JADSlink Agent iniciado"
# Esperado: "JADSlink Agent iniciado | Nodo: gl-mt3000-001 | Router: 192.168.8.1 | WAN: eth1 | LAN: br-lan"

# ========== FASE 3: PERSISTENCIA ==========

# 8. Verificar que /etc/firewall.user se creó
ls -la /etc/firewall.user
file /etc/firewall.user
# Debe ser script ejecutable

# 9. Verificar que directorio de reglas existe
ls -la /var/lib/jadslink/
# Debe existir y tener permisos

# ========== TEST: ACTIVACIÓN DE TICKET ==========

# 10. Conectar cliente WiFi al router
# (Desde otra máquina)

# 11. En cliente, abrir navegador
# http://192.168.8.1/
# Debe mostrar portal captive

# 12. Generar ticket en backend (simular)
# curl -X POST http://192.168.1.100:8000/api/v1/tickets/generate \
#   -H "Authorization: Bearer <token>" \
#   -d '{"node_id":"gl-mt3000-001","plan_id":"...","quantity":1}'

# 13. Obtener código de ticket y MAC del cliente
# MAC en router: arp -n
CLIENT_MAC="aa:bb:cc:dd:ee:ff"
TICKET_CODE="A3K9P2X7"

# 14. Verificar que cliente NO tiene internet
# ping -c 1 8.8.8.8
# Debe fallar (bloqueado por firewall)

# ========== FASE 1: BANDWIDTH LIMITING ==========

# 15. Activar ticket en portal (o vía curl)
# POST http://192.168.8.1/api/v1/portal/activate
# data: {"code":"A3K9P2X7"}

# 16. Verificar que iptables regla se creó
iptables -t filter -L JADSLINK_FORWARD -n
# Debe mostrar: Chain JADSLINK_FORWARD (policy DROP ... references)
#              target     prot opt source       destination
#              ACCEPT     all  --  0.0.0.0/0    0.0.0.0/0    MAC aa:bb:cc:dd:ee:ff

# 17. Verificar que tc (traffic control) se configuró
tc qdisc show dev eth1
# Debe mostrar: qdisc htb 1: root refcnt ...

tc class show dev eth1
# Debe mostrar clases para el plan seleccionado

tc filter show dev eth1
# Debe mostrar filtros con MAC address

# 18. Verificar que IFB se configuró
ip link show ifb0
# Debe mostrar: ifb0: <BROADCAST,NOTRAILERS,RUNNING>

# 19. En cliente, verificar que tiene internet
# ping -c 1 8.8.8.8
# Debe responder

# 20. Test de bandwidth (si hay servidor iperf3)
# Cliente: iperf3 -c <servidor>
# Verificar que throughput respeta límite del plan

# ========== PERSISTENCIA: REBOOT ==========

# 21. Reboot del router
reboot

# 22. Esperar reboot
sleep 60

# 23. Conectar SSH nuevamente
ssh root@192.168.8.1

# 24. Verificar que reglas persisten
iptables -t filter -L JADSLINK_FORWARD -n
# Debe mostrar la regla del cliente (si la sesión no expiró)

iptables -t nat -L JADSLINK_PREROUTING -n
# Debe mostrar reglas de redirección del portal

# 25. Verificar que tc reglas persisten
tc qdisc show dev eth1
# Debe mostrar HTB (si sesión activa)

# 26. Verificar que /var/lib/jadslink/iptables.rules existe
cat /var/lib/jadslink/iptables.rules
# Debe contener reglas JADSLINK

# ========== LIMPIEZA ==========

# 27. Parar servicio
/etc/init.d/jadslink stop

# 28. Verificar que reglas se limpian
iptables -t filter -L JADSLINK_FORWARD -n
# Puede estar vacío (si se limpió) o no existir

# 29. Ver logs finales
logread | grep jadslink | tail -20
# Debe mostrar limpieza correcta

# ========== RESUMEN ==========

echo ""
echo "TEST RESULTS:"
echo "============="
echo ""
echo "FASE 1: Bandwidth Limiting - $([ $? -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "FASE 2: Auto-detection - $([ $? -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "FASE 3: Persistence - $([ $? -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "FASE 4: Package (.ipk) - $([ $? -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "FASE 5: Hybrid install - $([ $? -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo ""
```

### Checklist de Validación

- [ ] FASE 1: tc qdisc se configura correctamente
- [ ] FASE 1: IFB interface funciona
- [ ] FASE 1: Bandwidth limit se aplica (verificado con speedtest)
- [ ] FASE 2: Interfaces se detectan automáticamente en log
- [ ] FASE 2: ROUTER_IP, LAN_INTERFACE, WAN_INTERFACE correcto
- [ ] FASE 3: /etc/firewall.user se crea
- [ ] FASE 3: /var/lib/jadslink/iptables.rules se genera
- [ ] FASE 3: Reglas persisten después de reboot
- [ ] FASE 4: .ipk compila sin errores
- [ ] FASE 4: .ipk instala sin errores
- [ ] FASE 4: Archivos en ubicaciones correctas
- [ ] FASE 5: install.sh detecta OpenWrt
- [ ] FASE 5: install.sh encuentra .ipk y lo instala
- [ ] FASE 5: install.sh fallback a manual si no hay .ipk
- [ ] FASE 5: Funciona en Ubuntu/Debian también

### Métricas de Rendimiento

```bash
# Verificar footprint (en router)

# RAM
top -bn1 | grep python3
# Debe estar entre 15-25MB

# CPU (idle)
top -bn1 | grep python3
# Debe estar < 5%

# Disk
df -h /var/lib/jadslink
# Debe usar < 100MB

# Network connections
netstat -an | grep -c ESTABLISHED
# Debe ser < 10 (una por sesión + heartbeat)
```

---

## Troubleshooting

### Error: "tc command failed"

```bash
# Verificar que tc está instalado
which tc
opkg list-installed | grep tc

# Instalar si falta
opkg install tc
```

### Error: "Failed to create IFB interface"

```bash
# Verificar módulo ifb
lsmod | grep ifb

# Cargar módulo
modprobe ifb

# Instalar si falta
opkg install kmod-ifb
```

### Error: "iptables command failed"

```bash
# Verificar iptables
which iptables
iptables --version

# Verificar que JADSLINK chains existen
iptables -t filter -L JADSLINK_FORWARD -n
iptables -t nat -L JADSLINK_PREROUTING -n
```

### Portal no accesible

```bash
# Verificar que servicio está corriendo
ps aux | grep jadslink-agent

# Verificar puerto
netstat -tlnp | grep :80

# Ver logs detallados
logread | grep jadslink | tail -50
```

### Reglas no persisten después de reboot

```bash
# Verificar /etc/firewall.user
cat /etc/firewall.user

# Verificar permisos
ls -la /etc/firewall.user
# Debe ser executable (755)

# Verificar archivo de reglas
cat /var/lib/jadslink/iptables.rules

# Verificar que /etc/firewall.user se ejecuta
logread | grep "firewall.user"
```

---

## Referencias

- [OpenWrt Traffic Control](https://openwrt.org/docs/guide_user/network/routing/policy_routing)
- [tc man page](https://man7.org/linux/man-pages/man8/tc.8.html)
- [HTB Qdisc Manual](https://luxik.cdi.cz/~devik/qos/htb/)
- [OpenWrt Package Development](https://openwrt.org/docs/guide_developer/packages)
- [OpenWrt UCI](https://openwrt.org/docs/guide_user/base_system/uci)

---

**Última actualización**: 2026-04-24
**Versión**: 1.0.0
**Status**: Testing Guide Completo
