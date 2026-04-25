#!/bin/bash
#
# Deploy JADSlink Agent to OpenWrt Device
# Transfiere los archivos del agente a un dispositivo OpenWrt vía SCP
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

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================
# VALIDACIONES INICIALES
# ============================================

print_header "JADSlink Agent Deploy to OpenWrt"

# Verificar que estamos en el directorio correcto
if [ ! -f "agent.py" ]; then
    print_error "agent.py no encontrado en directorio actual"
    print_info "Ejecuta este script desde /agent"
    exit 1
fi

print_ok "Directorio correcto: $(pwd)"

# ============================================
# PARÁMETROS
# ============================================

OPENWRT_HOST="${1:-10.0.0.1}"
OPENWRT_USER="${2:-root}"
OPENWRT_PORT="${3:-22}"

print_step "Parámetros de conexión"
echo "Host: $OPENWRT_HOST"
echo "Usuario: $OPENWRT_USER"
echo "Puerto: $OPENWRT_PORT"

# Permitir parámetros personalizados
if [ "$OPENWRT_HOST" = "-h" ] || [ "$OPENWRT_HOST" = "--help" ]; then
    echo "Uso: bash deploy-to-openwrt.sh [host] [usuario] [puerto]"
    echo ""
    echo "Ejemplos:"
    echo "  bash deploy-to-openwrt.sh                    # 10.0.0.1"
    echo "  bash deploy-to-openwrt.sh 192.168.0.209      # IP personalizada"
    echo "  bash deploy-to-openwrt.sh 192.168.0.209 root 22"
    exit 0
fi

# ============================================
# VERIFICAR CONECTIVIDAD SSH
# ============================================

print_header "Verificando Conectividad SSH"

print_step "Intentando conectar a $OPENWRT_USER@$OPENWRT_HOST:$OPENWRT_PORT"

if ! ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" -o ConnectTimeout=5 "exit 0" 2>/dev/null; then
    print_error "No se puede conectar a $OPENWRT_HOST"
    echo ""
    echo "Soluciones posibles:"
    echo "1. Verificar que OpenWrt está encendido y en la red"
    echo "2. Verificar IP con: ping $OPENWRT_HOST"
    echo "3. Permitir SSH en OpenWrt:"
    echo "   - Acceder a http://$OPENWRT_HOST (LuCI)"
    echo "   - System → System → Enable SSH server"
    echo "4. Si el password cambió:"
    echo "   ssh -p $OPENWRT_PORT root@$OPENWRT_HOST"
    exit 1
fi

print_ok "Conectado a $OPENWRT_HOST"

# ============================================
# VERIFICAR OPENWRT
# ============================================

print_header "Verificando Ambiente OpenWrt"

IS_OPENWRT=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "test -f /etc/openwrt_release && echo 1 || echo 0")

if [ "$IS_OPENWRT" = "1" ]; then
    print_ok "OpenWrt detectado"
    OPENWRT_VERSION=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "grep VERSION_ID /etc/openwrt_release | cut -d= -f2")
    print_info "Versión: $OPENWRT_VERSION"
else
    print_info "Sistema Linux estándar (no OpenWrt)"
fi

# ============================================
# VERIFICAR PYTHON
# ============================================

print_step "Verificando Python 3..."

PYTHON_VERSION=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "python3 --version 2>&1 | awk '{print \$2}'")

if [ -z "$PYTHON_VERSION" ]; then
    print_error "Python 3 no está instalado en OpenWrt"
    print_info "Instalar con: opkg install python3 python3-pip"
    exit 1
fi

print_ok "Python 3 instalado: $PYTHON_VERSION"

# ============================================
# LISTAR ARCHIVOS A TRANSFERIR
# ============================================

print_header "Archivos a Transferir"

FILES=(
    "agent.py"
    "config.py"
    "firewall.py"
    "portal.py"
    "session_manager.py"
    "sync.py"
    "cache.py"
    "requirements.txt"
    ".env.example"
    "README.md"
)

print_step "Verificando archivos..."

MISSING=()
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        print_ok "$file"
    else
        print_error "$file - FALTANTE"
        MISSING+=("$file")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    print_error "Archivos faltantes: ${MISSING[*]}"
    exit 1
fi

# ============================================
# TRANSFERIR ARCHIVOS
# ============================================

print_header "Transfiriendo Archivos vía SCP"

AGENT_DIR="/opt/jadslink"

print_step "Creando directorio remoto: $AGENT_DIR"
ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "mkdir -p $AGENT_DIR"
print_ok "Directorio creado"

print_step "Transfiriendo archivos..."

for file in "${FILES[@]}"; do
    echo -n "  ▶ $file... "
    if scp -P "$OPENWRT_PORT" -q "$file" "$OPENWRT_USER@$OPENWRT_HOST:$AGENT_DIR/"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        print_error "Error transferindo $file"
        exit 1
    fi
done

print_ok "Todos los archivos transferidos"

# ============================================
# CREAR CACHE DIRECTORY
# ============================================

print_step "Creando directorio de cache..."
ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "mkdir -p $AGENT_DIR/.cache"
print_ok "Cache directory creado"

# ============================================
# HACER EJECUTABLE
# ============================================

print_step "Configurando permisos..."
ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "chmod +x $AGENT_DIR/agent.py"
ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "chmod 600 $AGENT_DIR/.env 2>/dev/null || true"
print_ok "Permisos configurados"

# ============================================
# VERIFICAR INSTALACIÓN
# ============================================

print_header "Verificando Instalación Remota"

print_step "Listando archivos en $AGENT_DIR..."
ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "ls -lah $AGENT_DIR | grep -E '(agent|config|firewall|portal|\.env)'"

print_step "Verificando dependencias Python..."
IMPORTS=$(ssh -p "$OPENWRT_PORT" "$OPENWRT_USER@$OPENWRT_HOST" "python3 -c 'import requests, schedule, sqlite3; print(\"OK\")' 2>&1")

if echo "$IMPORTS" | grep -q "OK"; then
    print_ok "Dependencias Python verificadas"
else
    print_error "Faltan dependencias Python"
    echo "$IMPORTS"
    print_info "Instalar con: opkg install python3-pip && pip3 install requests schedule"
    exit 1
fi

# ============================================
# RESUMEN FINAL
# ============================================

print_header "✓ DEPLOY COMPLETADO"

echo "Archivos transferidos a: $AGENT_DIR"
echo ""
echo "Próximos pasos en OpenWrt:"
echo "1. Editar configuración .env:"
echo "   ssh root@$OPENWRT_HOST"
echo "   vi $AGENT_DIR/.env"
echo ""
echo "2. Iniciar el servicio:"
echo "   /etc/init.d/jadslink start"
echo ""
echo "3. Ver logs en tiempo real:"
echo "   logread -f | grep jadslink"
echo ""
echo "4. Verificar en dashboard que el nodo está 'online'"
echo ""

print_ok "¡Listo! El agente está instalado en OpenWrt"
