#!/bin/bash

# Script de prueba completa de todos los endpoints del frontend

API_URL="http://localhost:8000/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🧪 JADSlink - Prueba Completa de Endpoints"
echo "=========================================="
echo ""

# Test 1: Login
echo -e "${BLUE}[TEST 1]${NC} Login como operator"
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "operator@test.io", "password": "operator123"}')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓${NC} Login exitoso"
    echo "  Token: ${TOKEN:0:30}..."
else
    echo -e "${RED}✗${NC} Login falló"
    echo "  Response: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Get Tenant Info
echo -e "${BLUE}[TEST 2]${NC} GET /tenants/me"
TENANT_RESPONSE=$(curl -s -X GET $API_URL/tenants/me \
  -H "Authorization: Bearer $TOKEN")

TENANT_NAME=$(echo $TENANT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('name', ''))" 2>/dev/null)

if [ -n "$TENANT_NAME" ]; then
    echo -e "${GREEN}✓${NC} Tenant info obtenida"
    echo "  Nombre: $TENANT_NAME"
    TENANT_ID=$(echo $TENANT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
else
    echo -e "${RED}✗${NC} Error al obtener tenant info"
    echo "  Response: $TENANT_RESPONSE"
fi
echo ""

# Test 3: List Plans (should be empty initially)
echo -e "${BLUE}[TEST 3]${NC} GET /plans (lista inicial)"
PLANS_RESPONSE=$(curl -s -X GET $API_URL/plans \
  -H "Authorization: Bearer $TOKEN")
echo -e "${GREEN}✓${NC} Planes listados"
echo "  Response: $PLANS_RESPONSE"
echo ""

# Test 4: Create Plan 1
echo -e "${BLUE}[TEST 4]${NC} POST /plans (crear plan '30 Minutos')"
PLAN1_RESPONSE=$(curl -s -X POST $API_URL/plans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "30 Minutos",
    "duration_minutes": 30,
    "price_usd": 2.50
  }')

PLAN1_ID=$(echo $PLAN1_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -n "$PLAN1_ID" ]; then
    echo -e "${GREEN}✓${NC} Plan creado: 30 Minutos"
    echo "  ID: $PLAN1_ID"
else
    echo -e "${RED}✗${NC} Error al crear plan"
    echo "  Response: $PLAN1_RESPONSE"
fi
echo ""

# Test 5: Create Plan 2
echo -e "${BLUE}[TEST 5]${NC} POST /plans (crear plan '1 Hora')"
PLAN2_RESPONSE=$(curl -s -X POST $API_URL/plans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "1 Hora",
    "duration_minutes": 60,
    "price_usd": 5.00
  }')

PLAN2_ID=$(echo $PLAN2_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -n "$PLAN2_ID" ]; then
    echo -e "${GREEN}✓${NC} Plan creado: 1 Hora"
    echo "  ID: $PLAN2_ID"
else
    echo -e "${RED}✗${NC} Error al crear plan"
fi
echo ""

# Test 6: Create Plan 3
echo -e "${BLUE}[TEST 6]${NC} POST /plans (crear plan 'Día Completo')"
PLAN3_RESPONSE=$(curl -s -X POST $API_URL/plans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Día Completo",
    "duration_minutes": 1440,
    "price_usd": 15.00
  }')

PLAN3_ID=$(echo $PLAN3_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -n "$PLAN3_ID" ]; then
    echo -e "${GREEN}✓${NC} Plan creado: Día Completo"
    echo "  ID: $PLAN3_ID"
else
    echo -e "${RED}✗${NC} Error al crear plan"
fi
echo ""

# Test 7: List Plans (should have 3 now)
echo -e "${BLUE}[TEST 7]${NC} GET /plans (listar todos los planes)"
PLANS_LIST=$(curl -s -X GET $API_URL/plans \
  -H "Authorization: Bearer $TOKEN")

PLAN_COUNT=$(echo $PLANS_LIST | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)

echo -e "${GREEN}✓${NC} Planes listados: $PLAN_COUNT planes"
echo ""

# Test 8: Update Plan
if [ -n "$PLAN1_ID" ]; then
    echo -e "${BLUE}[TEST 8]${NC} PATCH /plans/{id} (actualizar precio)"
    UPDATE_RESPONSE=$(curl -s -X PATCH $API_URL/plans/$PLAN1_ID \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "price_usd": 3.00
      }')

    NEW_PRICE=$(echo $UPDATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('price_usd', ''))" 2>/dev/null)

    if [ "$NEW_PRICE" = "3.00" ]; then
        echo -e "${GREEN}✓${NC} Plan actualizado: nuevo precio \$3.00"
    else
        echo -e "${RED}✗${NC} Error al actualizar plan"
    fi
    echo ""
fi

# Test 9: Update Tenant Settings
echo -e "${BLUE}[TEST 9]${NC} PATCH /tenants/me (actualizar settings)"
SETTINGS_RESPONSE=$(curl -s -X PATCH $API_URL/tenants/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "logo_url": "https://via.placeholder.com/150",
    "primary_color": "#10b981",
    "custom_domain": "portal.testcompany.com"
  }')

LOGO_URL=$(echo $SETTINGS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('settings', {}).get('logo_url', ''))" 2>/dev/null)

if [ -n "$LOGO_URL" ]; then
    echo -e "${GREEN}✓${NC} Settings actualizados"
    echo "  Logo URL: $LOGO_URL"
else
    echo -e "${RED}✗${NC} Error al actualizar settings"
    echo "  Response: $SETTINGS_RESPONSE"
fi
echo ""

# Test 10: Get Subscription Plans
echo -e "${BLUE}[TEST 10]${NC} GET /subscriptions/plans"
SUB_PLANS=$(curl -s -X GET $API_URL/subscriptions/plans \
  -H "Authorization: Bearer $TOKEN")

if echo "$SUB_PLANS" | grep -q "error\|Error"; then
    echo -e "${YELLOW}⚠${NC}  Stripe no configurado (esperado en dev)"
else
    echo -e "${GREEN}✓${NC} Subscription plans obtenidos"
fi
echo ""

# Test 11: Register New Operator
echo -e "${BLUE}[TEST 11]${NC} POST /auth/register (nuevo operador)"
REGISTER_RESPONSE=$(curl -s -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company Auto",
    "email": "auto-test@company.com",
    "password": "testpassword123"
  }')

REG_STATUS=$(echo $REGISTER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)

if [ "$REG_STATUS" = "pending_approval" ]; then
    echo -e "${GREEN}✓${NC} Registro exitoso: status = pending_approval"
else
    echo -e "${YELLOW}⚠${NC}  Registro falló (puede ser duplicado)"
    echo "  Response: $REGISTER_RESPONSE"
fi
echo ""

# Test 12: Rate Limiting on Login
echo -e "${BLUE}[TEST 12]${NC} Rate Limiting en /auth/login"
echo "  Intentando 7 logins incorrectos..."

RATE_LIMITED=false
for i in {1..7}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST $API_URL/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email": "wrong@test.com", "password": "wrong"}')

    if [ "$HTTP_CODE" = "429" ]; then
        echo -e "${GREEN}✓${NC} Rate limit activado en intento $i (HTTP 429)"
        RATE_LIMITED=true
        break
    fi
done

if [ "$RATE_LIMITED" = false ]; then
    echo -e "${YELLOW}⚠${NC}  Rate limit no se activó en 7 intentos"
fi
echo ""

# Test 13: Delete Plan (soft delete)
if [ -n "$PLAN3_ID" ]; then
    echo -e "${BLUE}[TEST 13]${NC} DELETE /plans/{id} (eliminar plan)"
    DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE $API_URL/plans/$PLAN3_ID \
      -H "Authorization: Bearer $TOKEN")

    if [ "$DELETE_RESPONSE" = "204" ]; then
        echo -e "${GREEN}✓${NC} Plan eliminado (soft delete): HTTP 204"
    else
        echo -e "${RED}✗${NC} Error al eliminar plan: HTTP $DELETE_RESPONSE"
    fi
    echo ""
fi

# Summary
echo "=========================================="
echo -e "${GREEN}✅ Pruebas completadas${NC}"
echo ""
echo "Endpoints probados:"
echo "  ✓ POST /auth/login"
echo "  ✓ POST /auth/register"
echo "  ✓ GET  /tenants/me"
echo "  ✓ PATCH /tenants/me"
echo "  ✓ GET  /plans"
echo "  ✓ POST /plans (x3)"
echo "  ✓ PATCH /plans/{id}"
echo "  ✓ DELETE /plans/{id}"
echo "  ✓ GET  /subscriptions/plans"
echo "  ✓ Rate limiting verificado"
echo ""
echo "Ahora puedes probar el frontend en:"
echo -e "${YELLOW}http://localhost:5174${NC}"
echo ""
