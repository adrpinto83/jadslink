#!/bin/bash

# =============================================================================
# JADSlink Deployment Script para Hostinger
# =============================================================================
# Uso: ./deploy-hostinger.sh
# Este script automatiza la instalación de JADSlink en Hostinger
# =============================================================================

set -e  # Exit on error

echo "========================================"
echo "🚀 JADSlink Deployment Script"
echo "========================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$PROJECT_DIR/api"
DASHBOARD_DIR="$PROJECT_DIR/dashboard"
VENV_DIR="$API_DIR/venv"

# Funciones
log_info() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# =============================================================================
# 1. Verificar requisitos
# =============================================================================
echo ""
echo "📋 Verificando requisitos..."
echo ""

if ! command -v python3 &> /dev/null; then
    log_error "Python3 no está instalado"
    exit 1
fi
log_info "Python3 encontrado: $(python3 --version)"

if ! command -v pip3 &> /dev/null; then
    log_error "pip3 no está instalado"
    exit 1
fi
log_info "pip3 encontrado"

# =============================================================================
# 2. Crear archivo .env si no existe
# =============================================================================
echo ""
echo "🔐 Configurando variables de entorno..."
echo ""

if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.production" ]; then
        log_warn "Copiando .env.production → .env"
        cp "$PROJECT_DIR/.env.production" "$PROJECT_DIR/.env"

        echo ""
        echo "⚠️  IMPORTANTE:"
        echo "   1. Edita $PROJECT_DIR/.env"
        echo "   2. Actualiza DATABASE_URL con tus credenciales de Hostinger"
        echo "   3. Genera nuevas SECRET_KEY y TICKET_HMAC_SECRET"
        echo ""
        read -p "¿Continuar después de configurar .env? (s/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 1
        fi
    else
        log_error "Archivo .env no encontrado y no se puede copiar"
        exit 1
    fi
else
    log_info ".env ya configurado"
fi

# =============================================================================
# 3. Crear virtual environment
# =============================================================================
echo ""
echo "📦 Creando virtual environment..."
echo ""

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    log_info "Virtual environment creado"
else
    log_info "Virtual environment ya existe"
fi

# Activar venv
source "$VENV_DIR/bin/activate"
log_info "Virtual environment activado"

# =============================================================================
# 4. Instalar dependencias Python
# =============================================================================
echo ""
echo "📚 Instalando dependencias Python..."
echo ""

pip install --upgrade pip setuptools wheel
pip install -r "$API_DIR/requirements.txt"
log_info "Dependencias Python instaladas"

# =============================================================================
# 5. Ejecutar migraciones de base de datos
# =============================================================================
echo ""
echo "🗄️  Ejecutando migraciones de base de datos..."
echo ""

cd "$API_DIR"

# Verificar que la BD está disponible
echo "Verificando conexión a base de datos..."
python3 << 'EOF'
import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_db():
    try:
        db_url = os.getenv('DATABASE_URL')
        engine = create_async_engine(db_url, echo=False)
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
        print('✅ Base de datos conectada correctamente')
        await engine.dispose()
        return True
    except Exception as e:
        print(f'❌ Error de conexión: {e}')
        return False

result = asyncio.run(check_db())
exit(0 if result else 1)
EOF

if [ $? -ne 0 ]; then
    log_error "No se puede conectar a la base de datos"
    log_warn "Verifica: DATABASE_URL en .env"
    log_warn "Formato MySQL: mysql+aiomysql://user:pass@localhost:3306/db"
    log_warn "Usuario y contraseña en Hostinger"
    exit 1
fi

# Ejecutar migraciones
alembic upgrade head
log_info "Migraciones ejecutadas"

# =============================================================================
# 6. Seed de datos demo (OPCIONAL)
# =============================================================================
echo ""
echo "🌱 Aplicando seed de datos demo..."
echo ""

read -p "¿Aplicar seed de datos demo? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if [ -f "$API_DIR/scripts/reset_and_seed.py" ]; then
        python3 "$API_DIR/scripts/reset_and_seed.py"
        log_info "Seed completado"
    else
        log_warn "Script de seed no encontrado, omitiendo"
    fi
else
    log_info "Seed omitido"
fi

# =============================================================================
# 7. Compilar Frontend (OPCIONAL)
# =============================================================================
echo ""
echo "🎨 Compilando Dashboard..."
echo ""

if [ -d "$DASHBOARD_DIR" ]; then
    read -p "¿Compilar el Dashboard React? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        if ! command -v npm &> /dev/null; then
            log_warn "npm no está instalado, omitiendo Dashboard"
        else
            cd "$DASHBOARD_DIR"
            npm install
            npm run build
            log_info "Dashboard compilado en $DASHBOARD_DIR/dist"
        fi
    fi
else
    log_warn "Directorio dashboard no encontrado"
fi

# =============================================================================
# 8. Crear archivo de servicio systemd (OPCIONAL)
# =============================================================================
echo ""
echo "⚙️  Configuración de servicio systemd (opcional)..."
echo ""

read -p "¿Crear servicio systemd para autostart? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    VENV_PATH="$(cd "$VENV_DIR" && pwd)"
    SERVICE_FILE="/tmp/jadslink-api.service"

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=JADSlink API Service
After=network.target
Wants=network-online.target

[Service]
Type=notify
User=$(whoami)
WorkingDirectory=$API_DIR
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/gunicorn -w 4 -b 127.0.0.1:8000 main:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    log_warn "Archivo generado en: $SERVICE_FILE"
    log_warn "Para instalar como servicio systemd, corre:"
    log_warn "  sudo cp $SERVICE_FILE /etc/systemd/system/"
    log_warn "  sudo systemctl daemon-reload"
    log_warn "  sudo systemctl enable jadslink-api"
    log_warn "  sudo systemctl start jadslink-api"
fi

# =============================================================================
# 9. Resumen final
# =============================================================================
echo ""
echo "========================================"
echo "✅ Deployment completado"
echo "========================================"
echo ""
log_info "Pasos siguientes:"
echo ""
echo "1️⃣  Configurar Nginx (proxy reverso)"
echo "   Edita tu configuración de Hostinger para apuntar a 127.0.0.1:8000"
echo ""
echo "2️⃣  Iniciar API (elige UNA opción):"
echo ""
echo "   Opción A - PM2:"
echo "   npm install -g pm2"
echo "   cd $API_DIR"
echo "   source venv/bin/activate"
echo "   pm2 start 'gunicorn -w 4 -b 127.0.0.1:8000 main:app' --name jadslink-api"
echo ""
echo "   Opción B - Systemd (después de crear el servicio):"
echo "   sudo systemctl start jadslink-api"
echo ""
echo "3️⃣  Verificar que funcione:"
echo "   curl http://localhost:8000/health"
echo ""
echo "4️⃣  Acceder al dashboard:"
echo "   https://wheat-pigeon-347024.hostingersite.com"
echo ""
echo "📚 Documentación: $PROJECT_DIR/HOSTINGER_SETUP.md"
echo ""
