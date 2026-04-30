#!/bin/bash
################################################################################
#  RUN API IN PRODUCTION - Iniciar API con máxima disponibilidad
#  Solución robusta sin necesidad de systemd/sudo
################################################################################

PROJECT_DIR="/home/u938946830/jadslink-deploy"
API_DIR="$PROJECT_DIR/api"
LOG_FILE="/tmp/api.log"
PID_FILE="/tmp/jadslink-api.pid"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_banner() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║       JADSlink API - Production Startup & Monitoring           ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

start_api() {
    print_banner

    echo -e "${YELLOW}📍 INICIANDO API EN PRODUCCIÓN${NC}"
    echo ""

    # Limpiar procesos antiguos
    echo "1️⃣  Limpiando procesos anteriores..."
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "keep-api-alive.sh" 2>/dev/null || true
    sleep 2
    echo "   ✅ Procesos limpios"

    # Limpiar log viejo
    echo ""
    echo "2️⃣  Preparando logs..."
    rm -f "$LOG_FILE"
    touch "$LOG_FILE"
    echo "   ✅ Log file: $LOG_FILE"

    # Iniciar API
    echo ""
    echo "3️⃣  Iniciando Uvicorn..."
    cd "$API_DIR"

    # Usar nohup + disown para desacoplar del terminal
    nohup python3 -m uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        > "$LOG_FILE" 2>&1 &

    API_PID=$!
    echo "$API_PID" > "$PID_FILE"

    # Desacoplar del terminal
    disown $API_PID

    sleep 3

    # Verificar que está corriendo
    if ps -p $API_PID > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ API iniciada (PID: $API_PID)${NC}"
    else
        echo -e "   ${RED}❌ Error al iniciar API${NC}"
        echo "   Verificar logs:"
        tail -20 "$LOG_FILE"
        exit 1
    fi

    # Mostrar estado inicial
    echo ""
    echo -e "${YELLOW}📊 ESTADO INICIAL${NC}"
    echo ""

    tail -5 "$LOG_FILE" | grep -E "running|complete|error" || tail -5 "$LOG_FILE"

    echo ""
    echo -e "${GREEN}✅ API EN PRODUCCIÓN${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  • Ver logs:     tail -f $LOG_FILE"
    echo "  • Ver proceso:  ps aux | grep uvicorn"
    echo "  • Reiniciar:    $0"
    echo ""
}

# Ejecutar
start_api
