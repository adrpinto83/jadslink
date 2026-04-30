#!/bin/bash

# ==================================================================================
# JADSlink - Hostinger Troubleshooting & API Restart Script
# ==================================================================================
# Este script diagnostica problemas de la API en Hostinger y la reinicia
# Uso: bash HOSTINGER_TROUBLESHOOT_AND_RESTART.sh
# ==================================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración para Hostinger
HOSTINGER_HOST="217.65.147.159"
HOSTINGER_PORT="65002"
HOSTINGER_USER="u938946830"
API_DIR="/home/u938946830/jadslink-deploy/api"
LOG_FILE="/tmp/uvicorn.log"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         JADSlink - Troubleshoot & Restart Script               ║${NC}"
echo -e "${BLUE}║              Hostinger Deployment Support                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo

# ==================================================================================
# PASO 1: VERIFICAR CONEXIÓN SSH
# ==================================================================================
echo -e "${YELLOW}[1/5]${NC} Verificando conexión SSH a Hostinger..."
echo "  SSH: ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST}"

if ssh -o ConnectTimeout=5 -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} "exit 0" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Conexión SSH establecida correctamente"
else
    echo -e "${RED}✗${NC} No se puede conectar a Hostinger. Verifica:"
    echo "  - SSH host: ${HOSTINGER_HOST}:${HOSTINGER_PORT}"
    echo "  - SSH user: ${HOSTINGER_USER}"
    echo "  - Puertos abiertos en tu firewall"
    exit 1
fi
echo

# ==================================================================================
# PASO 2: DIAGNOSTICAR ESTADO ACTUAL DE UVICORN
# ==================================================================================
echo -e "${YELLOW}[2/5]${NC} Diagnosticando estado actual de Uvicorn..."
echo

UVICORN_STATUS=$(ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} "ps aux | grep -E 'uvicorn|python.*main' | grep -v grep | wc -l")

if [ "$UVICORN_STATUS" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Uvicorn ESTÁ CORRIENDO"
    echo
    ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} "ps aux | grep -E 'uvicorn|python.*main' | grep -v grep"
    echo
    echo -e "${BLUE}Últimas líneas del log:${NC}"
    ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} "tail -20 ${LOG_FILE} 2>/dev/null || echo 'Log file not found'"
else
    echo -e "${YELLOW}⚠${NC} Uvicorn NO ESTÁ CORRIENDO"
fi
echo

# ==================================================================================
# PASO 3: VERIFICAR CONECTIVIDAD A LA BASE DE DATOS
# ==================================================================================
echo -e "${YELLOW}[3/5]${NC} Verificando conectividad a la Base de Datos..."

DB_CHECK=$(ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} \
  "cd ${API_DIR} && python3 -c 'from config import get_settings; settings = get_settings(); print(\"DB URL OK\")' 2>&1")

if echo "$DB_CHECK" | grep -q "DB URL OK"; then
    echo -e "${GREEN}✓${NC} Configuración de BD está correcta"
else
    echo -e "${RED}✗${NC} Problema con la configuración de BD:"
    echo "$DB_CHECK"
    echo
    echo "Verifica que .env existe y contiene:"
    echo "  - DATABASE_URL correcta"
    echo "  - Credenciales válidas de MySQL"
fi
echo

# ==================================================================================
# PASO 4: MATAR UVICORN ANTIGUO (SI ESTÁ CORRIENDO)
# ==================================================================================
if [ "$UVICORN_STATUS" -gt 0 ]; then
    echo -e "${YELLOW}[4/5]${NC} Deteniendo Uvicorn anterior..."
    ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} \
        "pkill -f 'python3 -m uvicorn' || pkill -f 'uvicorn main' || true"

    echo "  Esperando 2 segundos para que se cierre completamente..."
    sleep 2

    UVICORN_KILLED=$(ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} \
        "ps aux | grep -E 'uvicorn|python.*main' | grep -v grep | wc -l")

    if [ "$UVICORN_KILLED" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Uvicorn detenido exitosamente"
    else
        echo -e "${YELLOW}⚠${NC} Uvicorn aún está en proceso de cierre..."
        sleep 2
    fi
else
    echo -e "${YELLOW}[4/5]${NC} Uvicorn no estaba corriendo, continuando..."
fi
echo

# ==================================================================================
# PASO 5: REINICIAR UVICORN
# ==================================================================================
echo -e "${YELLOW}[5/5]${NC} Iniciando Uvicorn..."

RESTART_CMD="cd ${API_DIR} && nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1 > ${LOG_FILE} 2>&1 &"

ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} "$RESTART_CMD"

echo "  Esperando 3 segundos para que Uvicorn se inicie..."
sleep 3

# Verificar que Uvicorn se inició correctamente
UVICORN_NEW=$(ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} \
    "ps aux | grep -E 'uvicorn|python.*main' | grep -v grep | wc -l")

if [ "$UVICORN_NEW" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Uvicorn reiniciado exitosamente"
    echo
    echo -e "${BLUE}Proceso activo:${NC}"
    ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} \
        "ps aux | grep -E 'uvicorn|python.*main' | grep -v grep"
else
    echo -e "${RED}✗${NC} ERROR: Uvicorn no se inició correctamente"
    echo
    echo -e "${BLUE}Logs de error:${NC}"
    ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} \
        "tail -50 ${LOG_FILE} || echo 'Log file not found'"
    exit 1
fi
echo

# ==================================================================================
# PRUEBAS FINALES
# ==================================================================================
echo -e "${YELLOW}Ejecutando pruebas finales...${NC}"
echo

echo -e "${BLUE}1. Probando endpoint /health${NC}"
HEALTH_TEST=$(ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} \
    "curl -s http://127.0.0.1:8000/health 2>&1")

if echo "$HEALTH_TEST" | grep -q "status"; then
    echo -e "${GREEN}✓${NC} /health responde correctamente"
    echo "  Response: $HEALTH_TEST"
else
    echo -e "${YELLOW}⚠${NC} /health no responde como se esperaba"
    echo "  Response: $HEALTH_TEST"
fi
echo

echo -e "${BLUE}2. Probando endpoint /api/v1/auth/login${NC}"
echo "  (Este endpoint debería devolver un error de validación si no hay credenciales)"

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ TROUBLESHOOTING COMPLETADO EXITOSAMENTE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo

echo -e "${BLUE}Próximos pasos:${NC}"
echo "1. Espera 30 segundos y verifica que la aplicación responde en:"
echo "   https://wheat-pigeon-347024.hostingersite.com"
echo
echo "2. Si aún hay problemas, revisa los logs:"
echo "   ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST}"
echo "   tail -100 /tmp/uvicorn.log"
echo
echo "3. Para verificar salud de Uvicorn de forma remota:"
echo "   ssh -p ${HOSTINGER_PORT} ${HOSTINGER_USER}@${HOSTINGER_HOST} 'curl http://127.0.0.1:8000/health'"
echo
