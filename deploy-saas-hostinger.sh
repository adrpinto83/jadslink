#!/bin/bash

################################################################################
#  DEPLOY SCRIPT SIMPLIFICADO: Planes SaaS en Hostinger
#  Versión robusta sin dependencias externas
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration - Usar directorio actual
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$PROJECT_DIR/api"

print_header() { echo -e "\n${BLUE}${1}${NC}\n"; }
print_success() { echo -e "${GREEN}✅ ${1}${NC}"; }
print_error() { echo -e "${RED}❌ ${1}${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  ${1}${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  ${1}${NC}"; }

################################################################################
# 1. VERIFICACIONES
################################################################################

print_header "PASO 1: VERIFICACIONES INICIALES"

[ -d "$API_DIR" ] || { print_error "No se encontró api/ en $PROJECT_DIR"; exit 1; }
[ -f "$API_DIR/.env" ] && print_success "Archivo .env encontrado" || print_warning ".env no encontrado"

# Extraer DB URL del .env
if [ -f "$API_DIR/.env" ]; then
    DB_URL=$(grep -E "^DATABASE_URL" "$API_DIR/.env" | cut -d'=' -f2)
    print_info "Database URL: ${DB_URL:0:50}..."
else
    print_error "No hay .env en $API_DIR"
    exit 1
fi

################################################################################
# 2. BACKUP
################################################################################

print_header "PASO 2: CREAR BACKUP"

BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_before_saas_$TIMESTAMP.sql"

print_info "Creando backup: $BACKUP_FILE"

# Parse connection string y crear backup
cd "$API_DIR"
python3 << 'PYEOF'
import os
import subprocess
import sys

DB_URL = os.environ.get('DB_URL', '')
backup_file = os.environ.get('BACKUP_FILE', '')

try:
    # Parse: mysql+aiomysql://user:pass@host:port/db
    parts = DB_URL.replace('mysql+aiomysql://', '').replace('postgresql+asyncpg://', '')
    if not '@' in parts:
        print("⚠️  No se pudo parsear BD, continuando sin backup")
        sys.exit(0)

    user_pass, rest = parts.split('@')
    user, password = user_pass.split(':')
    host_port, dbname = rest.split('/')
    host = host_port.split(':')[0]
    port = host_port.split(':')[1] if ':' in host_port else '3306'

    # Create backup
    with open(backup_file, 'w') as f:
        cmd = ['mysqldump', f'--user={user}', f'--password={password}',
               f'--host={host}', f'--port={port}', dbname]
        subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
    print(f"✅ Backup creado: {backup_file}")
except Exception as e:
    print(f"⚠️  Backup omitido: {e}")
PYEOF

export DB_URL
export BACKUP_FILE="$BACKUP_FILE"

################################################################################
# 3. MIGRACIÓN ALEMBIC
################################################################################

print_header "PASO 3: EJECUTAR MIGRACIÓN"

cd "$API_DIR"
print_info "Ejecutando: alembic upgrade head"

python3 -m alembic upgrade head

print_success "Migración completada"

################################################################################
# 4. SEED DE PLANES
################################################################################

print_header "PASO 4: INSERTAR 4 PLANES"

cd "$PROJECT_DIR"
print_info "Ejecutando seed..."

python3 api/scripts/seed_pricing_plans.py

print_success "Planes insertados"

################################################################################
# 5. VERIFICACIÓN FINAL
################################################################################

print_header "PASO 5: VERIFICACIÓN"

cd "$API_DIR"
python3 << 'PYEOF'
import sys
from sqlalchemy import create_engine, text
import os

DB_URL = os.environ.get('DB_URL', '')

try:
    # Usar sync URL
    sync_url = DB_URL.replace('+aiomysql', '').replace('+asyncpg', '')
    engine = create_engine(sync_url, echo=False)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM pricing_plans"))
        count = result.scalar()

        if count == 4:
            print(f"✅ {count} planes encontrados en BD")

            # Show plans
            result = conn.execute(text(
                "SELECT tier, name, monthly_price FROM pricing_plans ORDER BY sort_order"
            ))
            for row in result:
                print(f"   • {row[1]}: ${row[2]}/mes")
        else:
            print(f"❌ Error: {count} planes encontrados, esperaba 4")
            sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
PYEOF

export DB_URL

print_success "Verificación completada"

################################################################################
# 6. RESULTADO FINAL
################################################################################

cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        ✅ DEPLOYMENT DE PLANES SAAS EXITOSO EN HOSTINGER      ║
║                                                                ║
║  ✅ Migración completada                                       ║
║  ✅ 4 planes creados                                           ║
║  ✅ Verificaciones pasadas                                     ║
║                                                                ║
║  💰 PLANES DISPONIBLES:                                        ║
║     • Gratuito: $0/mes                                         ║
║     • Básico: $29/mes                                          ║
║     • Estándar: $79/mes ⭐                                     ║
║     • Pro: $199/mes                                            ║
║                                                                ║
║  🔗 VERIFICAR:                                                 ║
║     curl http://localhost:8000/api/v1/saas-plans              ║
║                                                                ║
║  ✨ ¡Todo listo para producción!                              ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

EOF

print_success "Deployment completado"
exit 0
