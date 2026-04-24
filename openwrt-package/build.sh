#!/bin/bash
#
# JADSlink Agent - OpenWrt Package Builder
# Descarga SDK, compila package y genera .ipk
#

set -e

# Configuración
SDK_VERSION="22.03.5"
TARGET="ramips/mt7621"
ARCH="ramips"
MACHINE="mt7621"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Verificar requisitos
check_requirements() {
    log_info "Verificando requisitos..."

    which wget > /dev/null || log_error "wget no encontrado"
    which tar > /dev/null || log_error "tar no encontrado"
    which gcc > /dev/null || log_error "gcc no encontrado"
    which make > /dev/null || log_error "make no encontrado"

    log_info "Requisitos verificados"
}

# Descargar SDK
download_sdk() {
    local sdk_file="openwrt-sdk-${SDK_VERSION}-${ARCH}-${MACHINE}_gcc-11.2.0_musl.Linux-x86_64.tar.xz"
    local sdk_url="https://downloads.openwrt.org/releases/${SDK_VERSION}/targets/${TARGET}/${sdk_file}"

    if [ -d "sdk" ]; then
        log_info "SDK ya existe en ./sdk, omitiendo descarga"
        return
    fi

    log_info "Descargando OpenWrt SDK..."
    wget -q -O "${sdk_file}" "${sdk_url}" || log_error "Fallo al descargar SDK"

    log_info "Extrayendo SDK..."
    tar xf "${sdk_file}"
    mv openwrt-sdk-* sdk

    log_info "SDK descargado y extraído"
}

# Setup feeds
setup_feeds() {
    log_info "Configurando feeds..."

    cd sdk

    mkdir -p feeds/custom
    cp -r ../ feeds/custom/jadslink-agent

    ./scripts/feeds update custom
    ./scripts/feeds install jadslink-agent

    log_info "Feeds configurados"
}

# Compilar package
compile_package() {
    log_info "Compilando package (esto puede tomar algunos minutos)..."

    # Copiar configuración
    cat > .config << EOF
CONFIG_ALL=y
CONFIG_ALL_NONSHARED=y
EOF

    # Compilar
    make package/feeds/custom/jadslink-agent/compile V=s

    log_info "Package compilado exitosamente"
}

# Copiar resultado
copy_result() {
    log_info "Copiando resultado..."

    mkdir -p ../dist

    # Encontrar el .ipk compilado
    ipk_file=$(find bin/packages -name "jadslink-agent*.ipk" 2>/dev/null | head -1)

    if [ -z "$ipk_file" ]; then
        log_error "No se encontró el archivo .ipk compilado"
    fi

    cp "$ipk_file" ../dist/

    log_info "Package copiado a: ../dist/$(basename $ipk_file)"
}

# Main
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════╗"
    echo "║   JADSlink Agent - OpenWrt Package Builder         ║"
    echo "║   Target: GL-MT3000 (ramips/mt7621)               ║"
    echo "║   SDK: OpenWrt ${SDK_VERSION}                         ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo ""

    check_requirements
    download_sdk
    setup_feeds
    compile_package
    copy_result

    echo ""
    echo -e "${GREEN}✓ Compilación completada${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "1. Transferir el .ipk al router:"
    echo "   scp dist/jadslink-agent*.ipk root@192.168.8.1:/tmp/"
    echo ""
    echo "2. Instalar en el router:"
    echo "   ssh root@192.168.8.1"
    echo "   opkg install /tmp/jadslink-agent*.ipk"
    echo ""
    echo "3. Configurar el agente:"
    echo "   uci set jadslink.agent.node_id='YOUR_NODE_ID'"
    echo "   uci set jadslink.agent.api_key='YOUR_API_KEY'"
    echo "   uci commit jadslink"
    echo ""
    echo "4. Iniciar el servicio:"
    echo "   /etc/init.d/jadslink start"
    echo "   /etc/init.d/jadslink enable"
    echo ""
}

main "$@"
