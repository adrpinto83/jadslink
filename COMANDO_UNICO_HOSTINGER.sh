#!/bin/bash

# =============================================================================
# JADSlink en Hostinger - Comando Único de Instalación
# =============================================================================
#
# INSTRUCCIONES:
# 1. Copiar este script a /home/u938946830/jadslink-deploy/
# 2. Editar las variables en la sección "CONFIGURACIÓN"
# 3. Ejecutar: bash COMANDO_UNICO_HOSTINGER.sh
#
# Este script automáticamente:
# - Crea virtual environment
# - Instala dependencias
# - Ejecuta migraciones
# - Aplica seed de datos
# - Levanta la API con PM2
#
# =============================================================================

set -e

echo ""
echo "╔═════════════════════════════════════════════════════════════╗"
echo "║  JADSlink Setup Automático para Hostinger (MySQL)           ║"
echo "╚═════════════════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# ⚙️ CONFIGURACIÓN (EDITA ESTOS VALORES)
# =============================================================================

# DATABASE CREDENTIALS (obtén de Hostinger panel → Bases de Datos)
DB_USER="u938946830_jadslink"          # ← REEMPLAZA
DB_PASSWORD="TuContraseña123"          # ← REEMPLAZA
DB_HOST="localhost"                    # Generalmente localhost
DB_PORT="3306"                         # Generalmente 3306
DB_NAME="u938946830_jadslink"          # ← REEMPLAZA

# SECURITY KEYS (genera con: python3 -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY="TuClaveSecreta32Caracteres"          # ← REEMPLAZA
TICKET_HMAC_SECRET="OtraClaveSecreta32Caracteres" # ← REEMPLAZA

# URLS
API_BASE_URL="https://wheat-pigeon-347024.hostingersite.com/api"
FRONTEND_URL="https://wheat-pigeon-347024.hostingersite.com"

# =============================================================================
# VARIABLES DERIVADAS (No tocar)
# =============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$PROJECT_DIR/api"
VENV_DIR="$API_DIR/venv"

# Construir DATABASE_URL (manejar caracteres especiales)
# Si la contraseña tiene caracteres especiales, necesita URL encoding
DATABASE_URL="mysql+aiomysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# =============================================================================
# FUNCIONES
# =============================================================================

log_info() {
    echo "✅ $1"
}

log_warn() {
    echo "⚠️  $1"
}

log_error() {
    echo "❌ $1"
}

# =============================================================================
# 1. VALIDAR CONFIGURACIÓN
# =============================================================================

echo ""
echo "1️⃣ Validando configuración..."
echo ""

# Verificar que las variables se editaron
if [[ "$DB_PASSWORD" == "TuContraseña123" ]]; then
    log_error "EDITA DB_PASSWORD en este script antes de ejecutar"
    exit 1
fi

if [[ "$SECRET_KEY" == "TuClaveSecreta32Caracteres" ]]; then
    log_error "EDITA SECRET_KEY en este script antes de ejecutar"
    exit 1
fi

log_info "Configuración validada"

# =============================================================================
# 2. CREAR ARCHIVO .env
# =============================================================================

echo ""
echo "2️⃣ Creando archivo .env..."
echo ""

cat > "$PROJECT_DIR/.env" << EOF
# Generado automáticamente por COMANDO_UNICO_HOSTINGER.sh
ENVIRONMENT=production
LOG_LEVEL=WARNING
DEBUG=false

# URLs
API_BASE_URL=$API_BASE_URL
FRONTEND_URL=$FRONTEND_URL

# DATABASE
DATABASE_URL=$DATABASE_URL

# SECURITY
SECRET_KEY=$SECRET_KEY
TICKET_HMAC_SECRET=$TICKET_HMAC_SECRET

# JWT
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15
REFRESH_TOKEN_EXPIRATION_DAYS=7

# STRIPE (opcional)
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# EMAIL (opcional)
RESEND_API_KEY=
EMAIL_FROM=noreply@wheat-pigeon-347024.hostingersite.com
EOF

log_info ".env creado"

# =============================================================================
# 3. CREAR VIRTUAL ENVIRONMENT
# =============================================================================

echo ""
echo "3️⃣ Creando virtual environment..."
echo ""

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    log_info "Virtual environment creado"
else
    log_info "Virtual environment ya existe"
fi

# Activar venv
source "$VENV_DIR/bin/activate"

# =============================================================================
# 4. INSTALAR DEPENDENCIAS
# =============================================================================

echo ""
echo "4️⃣ Instalando dependencias Python..."
echo ""

pip install --upgrade pip setuptools wheel > /dev/null 2>&1
log_info "pip actualizado"

pip install -r "$API_DIR/requirements.txt" > /dev/null 2>&1
log_info "Dependencias instaladas"

# Verificar aiomysql
python3 -c "import aiomysql; print('✅ aiomysql OK')"

# =============================================================================
# 5. VERIFICAR CONEXIÓN A BD
# =============================================================================

echo ""
echo "5️⃣ Verificando conexión a base de datos..."
echo ""

python3 << 'PYEOF'
import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def test_connection():
    try:
        engine = create_async_engine(
            os.getenv('DATABASE_URL'),
            echo=False,
            pool_pre_ping=True
        )
        async with engine.begin() as conn:
            result = await conn.execute(text('SELECT 1'))
        print('✅ Conexión a BD exitosa')
        await engine.dispose()
        return True
    except Exception as e:
        print(f'❌ Error de conexión: {e}')
        return False

success = asyncio.run(test_connection())
exit(0 if success else 1)
PYEOF

if [ $? -ne 0 ]; then
    log_error "No se puede conectar a la base de datos"
    log_warn "Verifica: DATABASE_URL en .env"
    log_warn "         Credenciales en Hostinger"
    exit 1
fi

# =============================================================================
# 6. EJECUTAR MIGRACIONES
# =============================================================================

echo ""
echo "6️⃣ Ejecutando migraciones de base de datos..."
echo ""

cd "$API_DIR"
alembic upgrade head

if [ $? -ne 0 ]; then
    log_error "Error en migraciones"
    exit 1
fi

log_info "Migraciones completadas"

# =============================================================================
# 7. APLICAR SEED DE DATOS (OPCIONAL)
# =============================================================================

echo ""
echo "7️⃣ Aplicando seed de datos (usuarios demo)..."
echo ""

read -p "¿Deseas aplicar datos de demostración? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    python3 scripts/reset_and_seed.py
    log_info "Seed completado"
else
    log_warn "Seed omitido"
fi

# =============================================================================
# 8. INSTALAR Y CONFIGURAR PM2
# =============================================================================

echo ""
echo "8️⃣ Instalando PM2..."
echo ""

if ! command -v pm2 &> /dev/null; then
    npm install -g pm2 > /dev/null 2>&1
    log_info "PM2 instalado"
else
    log_info "PM2 ya está instalado"
fi

# =============================================================================
# 9. LEVANTAR API CON PM2
# =============================================================================

echo ""
echo "9️⃣ Levantando API con PM2..."
echo ""

cd "$API_DIR"

# Matar proceso anterior si existe
pm2 delete jadslink-api 2>/dev/null || true

# Iniciar con PM2
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" \
    --name jadslink-api \
    --interpreter "$VENV_DIR/bin/python3"

# Guardar configuración de PM2
pm2 save

log_info "API levantada con PM2"

# =============================================================================
# 10. RESUMEN FINAL
# =============================================================================

echo ""
echo "╔═════════════════════════════════════════════════════════════╗"
echo "║  ✅ INSTALACIÓN COMPLETADA EXITOSAMENTE                     ║"
echo "╚═════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Información de la instalación:"
echo ""
echo "   Proyecto: $PROJECT_DIR"
echo "   Python: $(python3 --version)"
echo "   PM2: $(pm2 --version)"
echo ""

echo "🚀 Próximos pasos:"
echo ""
echo "   1. Verificar API:"
echo "      curl -s http://localhost:8000/health"
echo ""
echo "   2. Ver estado de PM2:"
echo "      pm2 status"
echo ""
echo "   3. Ver logs:"
echo "      pm2 logs jadslink-api"
echo ""
echo "   4. Acceder en navegador:"
echo "      https://wheat-pigeon-347024.hostingersite.com"
echo ""
echo "   5. Datos de acceso demo:"
echo "      Email: demo@jadslink.com"
echo "      Contraseña: demo123456"
echo ""

echo "✅ Sistema en producción"
echo ""
