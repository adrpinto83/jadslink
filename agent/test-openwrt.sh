#!/bin/bash
#
# JADSlink Agent Post-Setup Testing
# Valida que el agente está funcionando correctamente en OpenWrt
# Ejecutar como: bash test-openwrt.sh [openwrt-host]
#

set -e

# ============================================
# COLORES Y UTILIDADES
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================
# PARÁMETROS
# ============================================

OPENWRT_HOST="${1:-10.0.0.1}"
OPENWRT_USER="${2:-root}"
OPENWRT_PORT="${3:-22}"
AGENT_DIR="/opt/jadslink"

print_header "JADSlink Agent - Post-Setup Testing"

echo "Objetivo: OpenWrt: $OPENWRT_HOST"
echo "Usuario: $OPENWRT_USER"
echo "Agente: $AGENT_DIR"

# ============================================
# TEST 1: CONECTIVIDAD SSH
# ============================================

print_header "TEST 1: Conectividad SSH"

print_step "Conectando a $OPENWRT_HOST..."

if ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "exit 0" 2>/dev/null; then
    print_ok "Conexión SSH exitosa"
else
    print_error "No se puede conectar vía SSH"
    exit 1
fi

# ============================================
# TEST 2: ARCHIVOS DEL AGENTE
# ============================================

print_header "TEST 2: Archivos del Agente"

print_step "Verificando archivos..."

REQUIRED_FILES=(
    "agent.py"
    "config.py"
    "firewall.py"
    "portal.py"
    "sync.py"
    "cache.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    RESULT=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "test -f $AGENT_DIR/$file && echo 1 || echo 0")
    if [ "$RESULT" = "1" ]; then
        SIZE=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "wc -c < $AGENT_DIR/$file")
        print_ok "$file ($SIZE bytes)"
    else
        print_error "$file - NO ENCONTRADO"
    fi
done

# ============================================
# TEST 3: ARCHIVO .env
# ============================================

print_header "TEST 3: Configuración .env"

print_step "Verificando archivo .env..."

ENV_EXISTS=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "test -f $AGENT_DIR/.env && echo 1 || echo 0")

if [ "$ENV_EXISTS" = "1" ]; then
    print_ok ".env encontrado"

    print_step "Verificando variables requeridas..."

    VARS=("NODE_ID" "API_KEY" "SERVER_URL")

    for var in "${VARS[@]}"; do
        VALUE=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "grep ^$var $AGENT_DIR/.env | cut -d= -f2")
        if [ -n "$VALUE" ]; then
            # Ocultar valores sensibles
            if [ "$var" = "API_KEY" ]; then
                VALUE="${VALUE:0:15}..."
            fi
            print_ok "$var configurado"
        else
            print_error "$var no configurado en .env"
        fi
    done
else
    print_error ".env no encontrado"
fi

# ============================================
# TEST 4: SERVICIOS
# ============================================

print_header "TEST 4: Servicio JADSlink"

print_step "Verificando servicio..."

HAS_SERVICE=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "test -f /etc/init.d/jadslink && echo 1 || echo 0")

if [ "$HAS_SERVICE" = "1" ]; then
    print_ok "Init script encontrado"

    IS_RUNNING=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "ps | grep 'agent.py' | grep -v grep | wc -l")

    if [ "$IS_RUNNING" -gt 0 ]; then
        print_ok "✓ Agente está corriendo"
    else
        print_warning "Agente no está corriendo"
        print_info "Iniciar con: /etc/init.d/jadslink start"
    fi
else
    print_warning "Init script no encontrado"
fi

# ============================================
# TEST 5: PYTHON
# ============================================

print_header "TEST 5: Python y Dependencias"

print_step "Verificando Python 3..."

PYTHON_VERSION=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "python3 --version 2>&1 | awk '{print \$2}'")

if [ -n "$PYTHON_VERSION" ]; then
    print_ok "Python 3: $PYTHON_VERSION"
else
    print_error "Python 3 no encontrado"
fi

print_step "Verificando módulos Python..."

MODULES=("requests" "schedule" "sqlite3")

for module in "${MODULES[@]}"; do
    RESULT=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "python3 -c 'import $module' 2>&1 && echo 1 || echo 0")
    if [ "$RESULT" = "1" ]; then
        print_ok "$module disponible"
    else
        print_error "$module no disponible"
    fi
done

# ============================================
# TEST 6: RED
# ============================================

print_header "TEST 6: Configuración de Red"

print_step "Verificando interfaces..."

LAN_IP=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "ip addr show br-lan 2>/dev/null | grep 'inet ' | awk '{print \$2}' | cut -d/ -f1")

if [ -n "$LAN_IP" ]; then
    print_ok "IP LAN: $LAN_IP"
else
    print_warning "LAN IP no detectada"
fi

print_step "Verificando WiFi..."

SSID=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "uci get wireless.@wifi-iface[0].ssid 2>/dev/null")

if [ -n "$SSID" ]; then
    print_ok "SSID: $SSID"
else
    print_warning "SSID no encontrado"
fi

# ============================================
# TEST 7: FIREWALL
# ============================================

print_header "TEST 7: Firewall iptables"

print_step "Verificando cadenas iptables..."

FILTER_CHAIN=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "iptables -t filter -L JADSLINK_FORWARD 2>/dev/null | head -1 | grep -c 'JADSLINK_FORWARD' || echo 0")

if [ "$FILTER_CHAIN" != "0" ]; then
    print_ok "Cadena JADSLINK_FORWARD configurada"
else
    print_warning "Cadena JADSLINK_FORWARD no encontrada (se creará al activar tickets)"
fi

NAT_CHAIN=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "iptables -t nat -L JADSLINK_PREROUTING 2>/dev/null | head -1 | grep -c 'JADSLINK_PREROUTING' || echo 0")

if [ "$NAT_CHAIN" != "0" ]; then
    print_ok "Cadena JADSLINK_PREROUTING configurada"
else
    print_warning "Cadena JADSLINK_PREROUTING no encontrada (se creará al activar portal)"
fi

# ============================================
# TEST 8: PUERTO 80 (PORTAL)
# ============================================

print_header "TEST 8: Portal Captive (Puerto 80)"

print_step "Verificando puerto 80..."

PORT_80=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "netstat -tlnp 2>/dev/null | grep ':80' | wc -l")

if [ "$PORT_80" -gt 0 ]; then
    print_ok "Puerto 80 en escucha (portal activo)"
else
    print_warning "Puerto 80 no en escucha (portal iniciará al ejecutar agente)"
fi

# ============================================
# TEST 9: CACHE SQLite
# ============================================

print_header "TEST 9: Cache Local"

print_step "Verificando directorio de cache..."

CACHE_DIR_EXISTS=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "test -d $AGENT_DIR/.cache && echo 1 || echo 0")

if [ "$CACHE_DIR_EXISTS" = "1" ]; then
    print_ok "Directorio .cache existe"

    CACHE_SIZE=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "du -sh $AGENT_DIR/.cache 2>/dev/null | awk '{print \$1}'")
    print_info "Tamaño actual: $CACHE_SIZE"
else
    print_warning "Directorio .cache no existe (se creará automáticamente)"
fi

# ============================================
# TEST 10: LOGS
# ============================================

print_header "TEST 10: Logs del Sistema"

print_step "Últimas líneas de logs..."

if ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "command -v logread > /dev/null"; then
    LOGS=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "logread 2>/dev/null | grep -i jadslink | tail -5")
    if [ -n "$LOGS" ]; then
        echo "$LOGS"
    else
        print_info "Sin logs del agente aún"
    fi
else
    print_info "logread no disponible en este sistema"
fi

# ============================================
# RESUMEN FINAL
# ============================================

print_header "✓ TESTING COMPLETADO"

echo "Estado del Nodo: $OPENWRT_HOST"
echo ""

print_info "Comandos útiles:"
echo "  1. Ver logs en tiempo real:"
echo "     ssh root@$OPENWRT_HOST 'logread -f | grep jadslink'"
echo ""
echo "  2. Iniciar agente:"
echo "     ssh root@$OPENWRT_HOST '/etc/init.d/jadslink start'"
echo ""
echo "  3. Ver estado del agente:"
echo "     ssh root@$OPENWRT_HOST 'ps | grep agent.py'"
echo ""
echo "  4. Reiniciar agente:"
echo "     ssh root@$OPENWRT_HOST '/etc/init.d/jadslink restart'"
echo ""
echo "  5. Ver configuración:"
echo "     ssh root@$OPENWRT_HOST 'cat /opt/jadslink/.env'"
echo ""

print_ok "¡Testing completado! Verifica el dashboard para confirmar que el nodo está online."
