#!/bin/bash
################################################################################
#  SUPERVISOR API - Monitoreo permanente y auto-reinicio
#  Más inteligente que keep-api-alive.sh
################################################################################

PROJECT_DIR="/home/u938946830/jadslink-deploy"
API_DIR="$PROJECT_DIR/api"
LOG_FILE="/tmp/api.log"
SUPERVISOR_LOG="/tmp/supervisor-api.log"
PID_FILE="/tmp/jadslink-api.pid"

# Colors (para output)
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_sup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$SUPERVISOR_LOG"
}

check_api_health() {
    # Verificar si el proceso está corriendo
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            # Proceso está corriendo, pero verificar que esté respondiendo
            if curl -s -m 5 http://localhost:8000/api/v1/saas-plans > /dev/null 2>&1; then
                return 0  # API OK
            else
                return 2  # Proceso existe pero no responde
            fi
        fi
    fi
    return 1  # Proceso no existe
}

restart_api() {
    log_sup "⚠️  API CAÍDA - Reiniciando..."
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ API DOWN - Reiniciando...${NC}"

    # Matar todos los procesos uvicorn
    pkill -f "uvicorn main:app" 2>/dev/null || true
    sleep 3

    # Iniciar API
    cd "$API_DIR"
    nohup python3 -m uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --timeout-keep-alive 30 \
        --timeout-notify 30 \
        > "$LOG_FILE" 2>&1 &

    NEW_PID=$!
    echo "$NEW_PID" > "$PID_FILE"
    disown $NEW_PID

    sleep 3

    log_sup "✅ API REINICIADA (PID: $NEW_PID)"
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ API RESTARTED (PID: $NEW_PID)${NC}"
}

verify_initial_state() {
    log_sup "========== Supervisor API Started =========="
    echo -e "${YELLOW}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}              JADSlink API Supervisor (Auto-Restart)${NC}"
    echo -e "${YELLOW}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Supervisor Log: $SUPERVISOR_LOG"
    echo "API Log:        $LOG_FILE"
    echo ""
    echo "Verificando estado inicial..."
    sleep 2

    # Verificar estado
    check_api_health
    HEALTH=$?

    if [ $HEALTH -eq 0 ]; then
        echo -e "${GREEN}✅ API RUNNING${NC}"
        log_sup "✅ API is running and healthy"
    elif [ $HEALTH -eq 2 ]; then
        echo -e "${YELLOW}⚠️  API process exists but not responding - Restarting${NC}"
        restart_api
    else
        echo -e "${YELLOW}⚠️  API not running - Starting${NC}"
        restart_api
    fi

    echo ""
    echo "Supervisor is now monitoring API..."
    echo -e "${GREEN}====================================================== OK${NC}"
    echo ""
}

# Main loop
verify_initial_state

# Loop de monitoreo
CHECK_INTERVAL=30  # Verificar cada 30 segundos
FAIL_COUNT=0
MAX_FAILS=3  # Permitir 3 fallos antes de reiniciar (para evitar reiniciostoo frequent)

while true; do
    sleep $CHECK_INTERVAL

    check_api_health
    HEALTH=$?

    if [ $HEALTH -eq 0 ]; then
        # API está OK
        if [ $FAIL_COUNT -gt 0 ]; then
            FAIL_COUNT=0
            log_sup "✅ API is back to healthy state"
        fi
    else
        # API tiene problema
        FAIL_COUNT=$((FAIL_COUNT + 1))

        if [ $FAIL_COUNT -ge $MAX_FAILS ]; then
            restart_api
            FAIL_COUNT=0
        else
            log_sup "⚠️  API health check failed ($FAIL_COUNT/$MAX_FAILS)"
        fi
    fi
done
