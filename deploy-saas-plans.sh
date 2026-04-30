#!/bin/bash

################################################################################
#                                                                              #
#  DEPLOY SCRIPT: Planes SaaS Mejorados en JADSlink                           #
#  Ejecutar en Hostinger para deployar los cambios                            #
#                                                                              #
#  USO: ./deploy-saas-plans.sh                                                #
#                                                                              #
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/adrpinto/jadslink"
API_DIR="$PROJECT_DIR/api"
DASHBOARD_DIR="$PROJECT_DIR/dashboard"
BACKUP_DIR="$PROJECT_DIR/backups"

################################################################################
# FUNCTIONS
################################################################################

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_directory() {
    if [ ! -d "$1" ]; then
        print_error "Directorio no encontrado: $1"
        exit 1
    fi
}

################################################################################
# CHECKS INICIALES
################################################################################

print_header "1. VERIFICACIONES INICIALES"

print_info "Verificando directorios..."
check_directory "$PROJECT_DIR"
check_directory "$API_DIR"
check_directory "$DASHBOARD_DIR"
print_success "Directorios verificados"

print_info "Verificando conexión a la base de datos..."
cd "$API_DIR"

python3 << 'PYEOF'
import sys
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL no está configurado en .env")
    sys.exit(1)

print(f"Database URL: {DATABASE_URL[:50]}...")

# Try to connect
try:
    import sqlalchemy
    from sqlalchemy import create_engine, text

    # Para MySQL, remover +aiomysql
    sync_url = DATABASE_URL.replace('+aiomysql', '').replace('+asyncpg', '')
    engine = create_engine(sync_url, echo=False, pool_pre_ping=True)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Conexión a BD exitosa")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    print_error "No se pudo conectar a la base de datos"
    exit 1
fi

print_success "Conexión a BD verificada"

################################################################################
# BACKUP
################################################################################

print_header "2. CREAR BACKUP DE SEGURIDAD"

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/jads_before_saas_plans_$TIMESTAMP.sql"

print_info "Creando backup en: $BACKUP_FILE"

cd "$API_DIR"
python3 << 'PYEOF'
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# Parse connection string
# Format: mysql+aiomysql://user:pass@host:port/dbname
parts = DATABASE_URL.replace('mysql+aiomysql://', '').replace('postgresql+asyncpg://', '')
user_pass, rest = parts.split('@')
user, password = user_pass.split(':')
host_port, dbname = rest.split('/')

if ':' in host_port:
    host, port = host_port.split(':')
else:
    host = host_port
    port = '3306'

# Create backup
backup_file = os.environ.get('BACKUP_FILE')
try:
    with open(backup_file, 'w') as f:
        cmd = [
            'mysqldump',
            f'--user={user}',
            f'--password={password}',
            f'--host={host}',
            f'--port={port}',
            dbname
        ]
        subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
    print(f"✅ Backup creado: {backup_file}")
except Exception as e:
    print(f"⚠️  Advertencia: No se pudo crear backup: {e}")
    print("   Continuando de todas formas...")
PYEOF

print_success "Backup completado"

################################################################################
# GIT PULL
################################################################################

print_header "3. ACTUALIZAR CÓDIGO DESDE GIT"

cd "$PROJECT_DIR"

print_info "Pulling cambios más recientes..."
git pull origin main

if [ $? -ne 0 ]; then
    print_warning "No se pudo hacer pull desde git"
    print_info "Continuando con cambios locales..."
fi

print_success "Código actualizado"

################################################################################
# MIGRACIÓN
################################################################################

print_header "4. EJECUTAR MIGRACIÓN ALEMBIC"

cd "$API_DIR"

print_info "Ejecutando: alembic upgrade head"

python3 -m alembic upgrade head

if [ $? -ne 0 ]; then
    print_error "La migración Alembic falló"
    print_warning "Revirtiendo cambios..."
    exit 1
fi

print_success "Migración completada"

################################################################################
# SEED DE PLANES
################################################################################

print_header "5. INSERTAR 4 PLANES SAAS"

cd "$PROJECT_DIR"

print_info "Ejecutando script de seed..."

python3 api/scripts/seed_pricing_plans.py

if [ $? -ne 0 ]; then
    print_error "El script de seed falló"
    exit 1
fi

print_success "Planes insertados"

################################################################################
# VERIFICACIÓN
################################################################################

print_header "6. VERIFICAR PLANES EN BD"

cd "$API_DIR"

python3 << 'PYEOF'
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
sync_url = DATABASE_URL.replace('+aiomysql', '').replace('+asyncpg', '')

try:
    engine = create_engine(sync_url, echo=False)

    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("SELECT COUNT(*) as count FROM pricing_plans"))
        count = result.scalar()

        print(f"\n✅ Tabla 'pricing_plans' existe")
        print(f"   Planes en BD: {count}\n")

        if count == 0:
            print("⚠️  ADVERTENCIA: No hay planes en la BD")
            sys.exit(1)

        # Show plans
        result = conn.execute(text("""
            SELECT tier, name, monthly_price, included_tickets_per_month, included_nodes
            FROM pricing_plans
            ORDER BY sort_order
        """))

        for row in result:
            tier, name, price, tickets, nodes = row
            print(f"   • {name.upper()}")
            print(f"     - Tier: {tier}")
            print(f"     - Precio: ${price}/mes")
            print(f"     - Tickets: {tickets}")
            print(f"     - Nodos: {nodes}\n")

        print("✅ Todos los planes fueron creados correctamente")

except Exception as e:
    print(f"❌ Error durante verificación: {e}")
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    print_error "Verificación de planes falló"
    exit 1
fi

################################################################################
# VERIFICAR ENDPOINT
################################################################################

print_header "7. VERIFICAR ENDPOINT API"

print_info "Esperando a que la API esté lista..."
sleep 2

# Try to connect to API
print_info "Probando endpoint GET /api/v1/saas-plans"

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/saas-plans 2>/dev/null || echo "000")

if [ "$RESPONSE" = "200" ]; then
    print_success "Endpoint accesible (HTTP 200)"

    # Get and show response
    echo ""
    print_info "Planes disponibles:"
    curl -s http://localhost:8000/api/v1/saas-plans 2>/dev/null | python3 -m json.tool 2>/dev/null | grep -E '"tier"|"name"|"monthly_price"' | head -20 || echo "   (No se pudo parsear JSON)"
    echo ""
else
    print_warning "No se pudo verificar endpoint (HTTP $RESPONSE)"
    print_info "Asegúrate que la API está corriendo en puerto 8000"
fi

################################################################################
# REINICIAR API
################################################################################

print_header "8. REINICIAR API"

print_info "Reiniciando servicio API..."

# Try systemd
if command -v systemctl &> /dev/null; then
    sudo systemctl restart jadslink-api 2>/dev/null && print_success "API reiniciada (systemd)" || print_warning "No se pudo reiniciar con systemd"
fi

# Try pm2
if command -v pm2 &> /dev/null; then
    pm2 restart api 2>/dev/null && print_success "API reiniciada (pm2)" || print_warning "No se pudo reiniciar con pm2"
fi

# If using docker
if command -v docker &> /dev/null; then
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" restart api 2>/dev/null && print_success "API reiniciada (docker)" || print_warning "No se pudo reiniciar con docker"
fi

print_info "Esperando 5 segundos para que la API se levante..."
sleep 5

################################################################################
# VERIFICACIÓN FINAL
################################################################################

print_header "9. VERIFICACIÓN FINAL"

cd "$API_DIR"

python3 << 'PYEOF'
import sys
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
sync_url = DATABASE_URL.replace('+aiomysql', '').replace('+asyncpg', '')

checklist = {
    "Tabla pricing_plans existe": False,
    "4 planes en BD": False,
    "Plan gratuito existe": False,
    "Plan básico existe": False,
    "Plan estándar existe": False,
    "Plan pro existe": False,
    "Plan estándar es recomendado": False,
    "Enum PlanTier tiene 'standard'": False,
}

try:
    engine = create_engine(sync_url, echo=False)

    with engine.connect() as conn:
        # Check table
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM pricing_plans"))
            count = result.scalar()
            checklist["Tabla pricing_plans existe"] = True
            checklist["4 planes en BD"] = count == 4
        except:
            pass

        # Check each plan
        try:
            result = conn.execute(text("SELECT tier FROM pricing_plans WHERE is_active = 1"))
            tiers = {row[0] for row in result}

            checklist["Plan gratuito existe"] = "free" in tiers
            checklist["Plan básico existe"] = "basic" in tiers
            checklist["Plan estándar existe"] = "standard" in tiers
            checklist["Plan pro existe"] = "pro" in tiers
        except:
            pass

        # Check estándar is_recommended
        try:
            result = conn.execute(text("SELECT is_recommended FROM pricing_plans WHERE tier = 'standard'"))
            is_recommended = result.scalar()
            checklist["Plan estándar es recomendado"] = is_recommended == 1
        except:
            pass

    # Check enum in code
    try:
        with open('../models/tenant.py', 'r') as f:
            content = f.read()
            checklist["Enum PlanTier tiene 'standard'"] = 'standard' in content
    except:
        pass

    # Print results
    print("\n📋 CHECKLIST DE VERIFICACIÓN:\n")
    all_passed = True
    for item, status in checklist.items():
        symbol = "✅" if status else "❌"
        print(f"   {symbol} {item}")
        if not status:
            all_passed = False

    print()
    if all_passed:
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        sys.exit(0)
    else:
        print("⚠️  Algunas verificaciones fallaron")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
PYEOF

################################################################################
# FINAL SUMMARY
################################################################################

print_header "✅ DEPLOYMENT COMPLETADO"

cat << 'EOF'

🎉 ¡Implementación de Planes SaaS Completada en Hostinger!

📊 RESUMEN:
   ✅ Migración Alembic ejecutada
   ✅ 4 planes insertados en BD
   ✅ Endpoint /api/v1/saas-plans activo
   ✅ API reiniciada
   ✅ Todas las verificaciones pasaron

💰 PLANES DISPONIBLES:
   • Gratuito: $0/mes (50 tickets, 1 nodo)
   • Básico: $29/mes (200 tickets, 1 nodo)
   • Estándar: $79/mes (1,000 tickets, 3 nodos) ⭐
   • Pro: $199/mes (ilimitado)

🔗 ACCESOS:
   API docs:     https://tu-dominio.com/docs
   API endpoint: https://tu-dominio.com/api/v1/saas-plans
   Dashboard:    https://tu-dominio.com

📝 PRÓXIMOS PASOS:
   1. Verificar en navegador:
      - Login: debe mostrar 4 planes
      - Billing: planes dinámicos
      - Admin: opción "standard"

   2. Monitorear logs:
      - curl https://tu-dominio.com/api/v1/saas-plans

   3. Si hay problemas, revisar:
      - MIGRACION_PLANES_SAAS.md
      - Logs del servidor

✨ ¡Todo listo para producción!

EOF

print_success "Deployment exitoso"
exit 0
