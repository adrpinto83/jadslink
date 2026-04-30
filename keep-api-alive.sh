#!/bin/bash
################################################################################
#  KEEP API ALIVE - Auto-restart script for JADSlink API
#  Verifica cada 2 minutos si el API está corriendo
#  Si se cae, lo reinicia automáticamente
################################################################################

PROJECT_DIR="/home/u938946830/jadslink-deploy"
API_DIR="$PROJECT_DIR/api"
LOG_FILE="/tmp/api.log"
WATCHDOG_LOG="/tmp/api-watchdog.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_message() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$WATCHDOG_LOG"
}

check_and_restart() {
    # Verificar si el proceso está corriendo
    if ! ps aux | grep "uvicorn main:app" | grep -v grep > /dev/null; then
        echo -e "${RED}[$(date '+%H:%M:%S')] ❌ API DOWN - Reiniciando...${NC}"
        log_message "❌ API DOWN - Reiniciando..."

        # Matar procesos anteriores
        pkill -f "uvicorn main:app" 2>/dev/null || true
        sleep 2

        # Reiniciar
        cd "$API_DIR"
        nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > "$LOG_FILE" 2>&1 &

        sleep 3

        # Verificar que se inició
        if ps aux | grep "uvicorn main:app" | grep -v grep > /dev/null; then
            echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ API RESTARTED${NC}"
            log_message "✅ API RESTARTED successfully"
        else
            echo -e "${RED}[$(date '+%H:%M:%S')] ❌ API FAILED TO START${NC}"
            log_message "❌ API FAILED TO START - Check logs"
        fi
    else
        echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ API OK${NC}"
    fi
}

# Banner
clear
echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║                JADSlink API Watchdog (Keep Alive)              ║${NC}"
echo -e "${YELLOW}║  Verifying API status every 2 minutes and auto-restarting...  ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📝 Logs: $LOG_FILE"
echo -e "📊 Watchdog log: $WATCHDOG_LOG"
echo ""
log_message "========== JADSlink API Watchdog Started =========="

# Loop principal
while true; do
    check_and_restart
    sleep 120  # Verificar cada 2 minutos
done
