#!/bin/bash
################################################################################
#  CHECK API STATUS - Ver el estado actual del API en producción
################################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Remote info
REMOTE_HOST="217.65.147.159"
REMOTE_PORT="65002"
REMOTE_USER="u938946830"
PROJECT_DIR="/home/u938946830/jadslink-deploy"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          JADSlink API Status en Hostinger                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST << 'EOSSH'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}📍 ESTADO DEL API${NC}"
echo ""

# 1. Verificar API
if ps aux | grep "uvicorn main:app" | grep -v grep > /dev/null; then
    API_PID=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')
    echo -e "${GREEN}✅ API CORRIENDO${NC}"
    echo "   PID: $API_PID"
    echo "   Cmd: python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"
else
    echo -e "${RED}❌ API OFFLINE${NC}"
    echo "   El proceso no está corriendo"
fi

echo ""
echo -e "${YELLOW}📊 ESTADO DE LA BD${NC}"
echo ""

python3 << 'PYEOF'
import pymysql, os
from dotenv import load_dotenv

load_dotenv('/home/u938946830/jadslink-deploy/api/.env')
db_url = os.getenv('DATABASE_URL')

try:
    parts = db_url.replace('mysql+aiomysql://', '')
    user_pass, rest = parts.split('@')
    user, password = user_pass.split(':')
    host_port, dbname = rest.split('/')
    host = "127.0.0.1"
    port = int(host_port.split(':')[1]) if ':' in host_port else 3306

    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, database=dbname
    )
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"\033[0;32m✅ BD CONECTADA\033[0m")
    print(f"   Version: {version[0]}")

    cursor.execute("SELECT COUNT(*) FROM pricing_plans")
    count = cursor.fetchone()[0]
    print(f"   Planes en BD: {count}")

    # Mostrar planes
    cursor.execute("SELECT tier, name, monthly_price FROM pricing_plans ORDER BY sort_order")
    rows = cursor.fetchall()
    print("\n   Planes disponibles:")
    for tier, name, price in rows:
        print(f"     • {name}: ${price}/mes")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"\033[0;31m❌ ERROR BD\033[0m")
    print(f"   {e}")
PYEOF

echo ""
echo -e "${YELLOW}👁️  WATCHDOG (Auto-Reinicio)${NC}"
echo ""

if ps aux | grep "keep-api-alive.sh" | grep -v grep > /dev/null; then
    echo -e "${GREEN}✅ WATCHDOG ACTIVO${NC}"
    echo "   Verifica cada 2 minutos si el API está corriendo"
    echo "   Auto-reinicia si se cae"
else
    echo -e "${RED}❌ WATCHDOG INACTIVO${NC}"
    echo "   Ejecutar: cd /home/u938946830/jadslink-deploy && nohup bash keep-api-alive.sh > /tmp/watchdog.log 2>&1 &"
fi

echo ""
echo -e "${YELLOW}📝 LOGS RECIENTES${NC}"
echo ""

echo "API Log (últimas 5 líneas):"
tail -5 /tmp/api.log 2>/dev/null | tail -3

echo ""
echo "Watchdog Log (últimas 5 líneas):"
tail -5 /tmp/api-watchdog.log 2>/dev/null | tail -3 || echo "   (sin logs aún)"

EOSSH

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
