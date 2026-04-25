#!/bin/bash
#
# JADSlink OpenWrt Configuration Script
# Configura completamente un dispositivo OpenWrt como nodo JADSlink
# Ejecutar como: bash openwrt-setup.sh
#

set -e

# ============================================
# COLORES Y UTILIDADES
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}======================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================================${NC}\n"
}

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_ok() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# ============================================
# VALIDACIONES INICIALES
# ============================================

print_header "JADSlink OpenWrt Configuration"

if [[ $EUID -ne 0 ]]; then
    print_error "Este script debe ejecutarse como root"
    echo "Intenta: sudo bash openwrt-setup.sh"
    exit 1
fi

print_ok "Ejecutando como root"

# ============================================
# FASE 1: RECOPILAR INFORMACIÓN
# ============================================

print_header "FASE 1: Configuración Inicial"

print_step "Ingresa las credenciales del nodo del dashboard"
echo ""

read -p "NODE_ID (ej: 33bdb4bd-7516-4bdd-9133-a1b4743a0a8d): " NODE_ID
read -p "API_KEY (ej: sk_live_1B716280474F323FA05C79...): " API_KEY
read -p "SERVER_URL (ej: http://192.168.0.X:8000): " SERVER_URL

# Validar formato
if [[ ! $NODE_ID =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    print_error "NODE_ID inválido"
    exit 1
fi

if [[ ! $API_KEY =~ ^sk_live_ ]]; then
    print_error "API_KEY debe comenzar con 'sk_live_'"
    exit 1
fi

if [[ ! $SERVER_URL =~ ^https?:// ]]; then
    print_error "SERVER_URL debe comenzar con http:// o https://"
    exit 1
fi

print_ok "Credenciales validadas"

# Detectar interfaces de red
print_step "Detectando interfaces de red..."

if check_command uci; then
    # OpenWrt con UCI
    ROUTER_IP=$(uci get network.lan.ipaddr 2>/dev/null || echo "10.0.0.1")
    LAN_INTERFACE="br-lan"
    WAN_INTERFACE=$(uci get network.wan.ifname 2>/dev/null || echo "eth0.2")
    IS_OPENWRT=1
else
    # Sistema Linux estándar
    ROUTER_IP="10.0.0.1"
    LAN_INTERFACE="eth0"
    WAN_INTERFACE="eth1"
    IS_OPENWRT=0
fi

print_ok "Router IP: $ROUTER_IP"
print_ok "LAN Interface: $LAN_INTERFACE"
print_ok "WAN Interface: $WAN_INTERFACE"

# ============================================
# FASE 2: ACTUALIZAR REPOSITORIOS
# ============================================

if [ $IS_OPENWRT -eq 1 ]; then
    print_header "FASE 2: Actualizar Repositorios (OpenWrt)"

    print_step "Ejecutando opkg update..."
    opkg update 2>/dev/null || print_warning "Algunos repositorios no disponibles"
    print_ok "Repositorios actualizados"
else
    print_header "FASE 2: Actualizar Repositorios (Linux estándar)"

    if check_command apt-get; then
        print_step "Ejecutando apt-get update..."
        apt-get update -qq
        print_ok "Repositorios actualizados"
    fi
fi

# ============================================
# FASE 3: INSTALAR DEPENDENCIAS DEL SISTEMA
# ============================================

print_header "FASE 3: Instalar Dependencias"

print_step "Verificando Python 3..."
if ! check_command python3; then
    print_step "Instalando Python 3..."
    if [ $IS_OPENWRT -eq 1 ]; then
        opkg install python3 python3-pip python3-sqlite3
    else
        apt-get install -y python3 python3-pip python3-venv
    fi
fi
print_ok "Python 3 instalado"

print_step "Verificando herramientas de red..."
if [ $IS_OPENWRT -eq 1 ]; then
    opkg install iptables-mod-ipopt iptables-mod-conntrack-extra 2>/dev/null || true
    opkg install tc kmod-ifb kmod-sched-core kmod-sched-htb 2>/dev/null || true
fi
print_ok "Herramientas de red instaladas"

# ============================================
# FASE 4: INSTALAR DEPENDENCIAS PYTHON
# ============================================

print_header "FASE 4: Instalar Dependencias Python"

print_step "Instalando paquetes Python..."
pip3 install -q requests schedule python-dotenv 2>/dev/null || pip install -q requests schedule python-dotenv
print_ok "Paquetes Python instalados"

# ============================================
# FASE 5: CONFIGURAR RED (OpenWrt UCI)
# ============================================

if [ $IS_OPENWRT -eq 1 ]; then
    print_header "FASE 5: Configurar Red (OpenWrt)"

    print_step "Configurando LAN..."
    uci set network.lan.ipaddr='10.0.0.1'
    uci set network.lan.netmask='255.255.255.0'
    uci set network.lan.gateway='192.168.0.1'
    uci set network.lan.dns='8.8.8.8 1.1.1.1'
    print_ok "LAN configurada: 10.0.0.1/24"

    print_step "Configurando WiFi abierto..."
    uci set wireless.radio0.disabled='0'
    uci set wireless.@wifi-iface[0].ssid='JADSlink-WiFi'
    uci set wireless.@wifi-iface[0].encryption='none'
    uci set wireless.@wifi-iface[0].network='lan'
    uci set wireless.@wifi-iface[0].mode='ap'
    uci set wireless.@wifi-iface[0].disabled='0'
    print_ok "WiFi configurado: JADSlink-WiFi (abierto)"

    print_step "Configurando DHCP..."
    uci set dhcp.lan.start='100'
    uci set dhcp.lan.limit='150'
    uci set dhcp.lan.leasetime='12h'
    print_ok "DHCP configurado"

    print_step "Aplicando cambios UCI..."
    uci commit network
    uci commit wireless
    uci commit dhcp
    print_ok "Cambios aplicados"

    print_step "Reiniciando servicios..."
    /etc/init.d/network restart 2>/dev/null || true
    wifi reload 2>/dev/null || true
    /etc/init.d/dnsmasq restart 2>/dev/null || true
    print_ok "Servicios reiniciados"
else
    print_header "FASE 5: Configurar Red (Linux estándar)"
    print_warning "Saltando configuración UCI (no es OpenWrt)"
fi

# ============================================
# FASE 6: CREAR DIRECTORIO DEL AGENTE
# ============================================

print_header "FASE 6: Crear Directorio del Agente"

AGENT_DIR="/opt/jadslink"
print_step "Creando directorio: $AGENT_DIR"

if [ ! -d "$AGENT_DIR" ]; then
    mkdir -p "$AGENT_DIR"
    print_ok "Directorio creado"
else
    print_ok "Directorio ya existe"
fi

# ============================================
# FASE 7: CREAR ARCHIVO .env
# ============================================

print_header "FASE 7: Configurar Agente JADSlink"

print_step "Creando archivo .env..."

cat > "$AGENT_DIR/.env" << EOF
# JADSlink Agent Configuration
# Generado automáticamente el $(date)

# Node Identity
NODE_ID=$NODE_ID
API_KEY=$API_KEY

# Server Connection
SERVER_URL=$SERVER_URL

# Network Configuration
ROUTER_IP=$ROUTER_IP
LAN_INTERFACE=$LAN_INTERFACE
WAN_INTERFACE=$WAN_INTERFACE

# Portal
PORTAL_PORT=80
PORTAL_HOST=0.0.0.0

# Intervals (seconds)
HEARTBEAT_INTERVAL=30
SYNC_INTERVAL=300
EXPIRE_INTERVAL=60

# Storage
CACHE_DIR=$AGENT_DIR/.cache
EOF

print_ok ".env creado: $AGENT_DIR/.env"

chmod 600 "$AGENT_DIR/.env"
print_ok "Permisos configurados (600)"

# ============================================
# FASE 8: CREAR CACHE DIRECTORY
# ============================================

print_header "FASE 8: Crear Directorio de Cache"

CACHE_DIR="$AGENT_DIR/.cache"
print_step "Creando directorio de cache..."

mkdir -p "$CACHE_DIR"
print_ok "Directorio de cache creado"

# ============================================
# FASE 9: CREAR INIT SCRIPT
# ============================================

print_header "FASE 9: Crear Service Init Script"

if [ $IS_OPENWRT -eq 1 ]; then
    print_step "Creando OpenWrt init script..."

    cat > /etc/init.d/jadslink << 'INIT_EOF'
#!/bin/sh /etc/rc.common
START=99
STOP=10
USE_PROCD=1

PROG=/usr/bin/python3
AGENT=/opt/jadslink/agent.py

start_service() {
    procd_open_instance
    procd_set_param command $PROG $AGENT
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_set_param env PYTHONUNBUFFERED=1
    procd_close_instance
}

stop_service() {
    # Limpiar reglas iptables
    iptables -t nat -F JADSLINK_PREROUTING 2>/dev/null || true
    iptables -t filter -F JADSLINK_FORWARD 2>/dev/null || true
}
INIT_EOF

    chmod +x /etc/init.d/jadslink
    print_ok "Init script creado: /etc/init.d/jadslink"

    print_step "Habilitando auto-inicio..."
    /etc/init.d/jadslink enable
    print_ok "Auto-inicio habilitado"

else
    print_step "Creando systemd service..."

    cat > /etc/systemd/system/jadslink.service << 'SYSTEMD_EOF'
[Unit]
Description=JADSlink Agent
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/jadslink/agent.py
Restart=always
RestartSec=10
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

    systemctl daemon-reload
    systemctl enable jadslink
    print_ok "Systemd service creado"
fi

# ============================================
# RESUMEN FINAL
# ============================================

print_header "✓ CONFIGURACIÓN COMPLETADA"

echo "Información del Nodo:"
echo "  NODE_ID: $NODE_ID"
echo "  API_KEY: ${API_KEY:0:15}..."
echo "  SERVER_URL: $SERVER_URL"
echo ""
echo "Configuración de Red:"
echo "  LAN IP: 10.0.0.1/24"
echo "  SSID: JADSlink-WiFi (sin contraseña)"
echo "  DHCP: 10.0.0.100 - 10.0.0.250"
echo ""
echo "Directorio del Agente: $AGENT_DIR"
echo ""
echo "Próximos pasos:"
echo "1. Copiar archivos del agente a $AGENT_DIR"
echo "   (agent.py, config.py, firewall.py, portal.py, etc.)"
echo ""
echo "2. Iniciar el servicio:"
if [ $IS_OPENWRT -eq 1 ]; then
    echo "   /etc/init.d/jadslink start"
else
    echo "   systemctl start jadslink"
fi
echo ""
echo "3. Ver logs:"
if [ $IS_OPENWRT -eq 1 ]; then
    echo "   logread -f | grep jadslink"
else
    echo "   journalctl -u jadslink -f"
fi
echo ""
echo "4. Verificar en dashboard:"
echo "   Nodo debe aparecer como 'online' en ~30 segundos"
echo ""

print_ok "¡Listo para instalar el agente!"
