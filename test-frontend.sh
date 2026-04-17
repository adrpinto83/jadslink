#!/bin/bash

# Script de prueba rápida del frontend JADSlink

set -e

echo "🧪 JADSlink Frontend Testing Script"
echo "===================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar Docker Compose
echo "📦 Verificando servicios Docker..."
if docker compose ps | grep -q "jadslink-api-1.*Up"; then
    echo -e "${GREEN}✓${NC} API corriendo en puerto 8000"
else
    echo -e "${RED}✗${NC} API no está corriendo"
    echo "  Ejecuta: docker compose up -d"
    exit 1
fi

if docker compose ps | grep -q "jadslink-db-1.*healthy"; then
    echo -e "${GREEN}✓${NC} PostgreSQL corriendo en puerto 5433"
else
    echo -e "${RED}✗${NC} PostgreSQL no está corriendo o no está saludable"
    exit 1
fi

if docker compose ps | grep -q "jadslink-redis-1.*Up"; then
    echo -e "${GREEN}✓${NC} Redis corriendo en puerto 6379"
else
    echo -e "${RED}✗${NC} Redis no está corriendo"
    exit 1
fi

# 2. Verificar API health
echo ""
echo "🔍 Verificando API health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/v1/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✓${NC} API respondiendo correctamente"
    echo "  $HEALTH_RESPONSE"
else
    echo -e "${RED}✗${NC} API no responde correctamente"
    exit 1
fi

# 3. Verificar datos seed
echo ""
echo "🌱 Verificando datos de prueba..."
SUPERADMIN_EXISTS=$(docker compose exec -T db psql -U jads -d jadslink -tAc "SELECT COUNT(*) FROM users WHERE email = 'admin@jads.io';")
if [ "$SUPERADMIN_EXISTS" -eq "1" ]; then
    echo -e "${GREEN}✓${NC} Superadmin existe (admin@jads.io / admin123)"
else
    echo -e "${YELLOW}⚠${NC}  Superadmin no existe. Ejecutando seed..."
    docker compose exec -T api python scripts/seed.py
fi

OPERATOR_EXISTS=$(docker compose exec -T db psql -U jads -d jadslink -tAc "SELECT COUNT(*) FROM users WHERE email = 'operator@test.io';")
if [ "$OPERATOR_EXISTS" -eq "1" ]; then
    echo -e "${GREEN}✓${NC} Operator existe (operator@test.io / operator123)"
else
    echo -e "${YELLOW}⚠${NC}  Operator de prueba no existe (se creará al registrarse)"
fi

# 4. Verificar dependencias del dashboard
echo ""
echo "📦 Verificando dashboard..."
cd dashboard

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠${NC}  node_modules no existe. Instalando dependencias..."
    npm install
else
    echo -e "${GREEN}✓${NC} node_modules existe"
fi

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC}  .env no existe. Creando..."
    echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env
else
    echo -e "${GREEN}✓${NC} .env existe"
fi

# 5. Instrucciones finales
echo ""
echo "✅ Verificación completada!"
echo ""
echo "🚀 Para iniciar el dashboard:"
echo -e "${YELLOW}   cd dashboard && npm run dev${NC}"
echo ""
echo "📖 Luego abre el navegador en:"
echo -e "${YELLOW}   http://localhost:5173${NC}"
echo ""
echo "📋 Credenciales de prueba:"
echo "   Superadmin: admin@jads.io / admin123"
echo "   Operator:   operator@test.io / operator123"
echo ""
echo "📚 Guía completa de pruebas:"
echo -e "${YELLOW}   cat TESTING_GUIDE.md${NC}"
echo ""
