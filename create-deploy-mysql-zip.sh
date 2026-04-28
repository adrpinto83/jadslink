#!/bin/bash

# =============================================================================
# Create Optimized JADSlink Deployment Package (MySQL Version)
# =============================================================================
# Uso: ./create-deploy-mysql-zip.sh
# Genera un TAR.GZ optimizado para Hostinger con MySQL
# =============================================================================

set -e

echo "========================================"
echo "📦 Creando ZIP para despliegue (MySQL)..."
echo "========================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$PROJECT_DIR/jadslink-deploy-mysql.tar.gz"
TEMP_DIR=$(mktemp -d)
DEPLOY_DIR="$TEMP_DIR/jadslink-deploy"

echo "📁 Directorio temporal: $TEMP_DIR"
echo ""

# Crear estructura del proyecto en temp
mkdir -p "$DEPLOY_DIR"

# Archivos y directorios a incluir
echo "📋 Copiando archivos..."

# Directorios principales (usar rsync para excluir directorios)
rsync -av --exclude="__pycache__" --exclude=".pytest_cache" --exclude="venv" --exclude=".env" "$PROJECT_DIR/api/" "$DEPLOY_DIR/api/"
rsync -av --exclude="node_modules" --exclude="dist" --exclude=".env" "$PROJECT_DIR/dashboard/" "$DEPLOY_DIR/dashboard/" 2>/dev/null || echo "⚠️  Directorio dashboard no encontrado"
rsync -av "$PROJECT_DIR/agent/" "$DEPLOY_DIR/agent/" 2>/dev/null || echo "⚠️  Directorio agent no encontrado (opcional)"

# Archivos de configuración y documentación
cp "$PROJECT_DIR/.env.example" "$DEPLOY_DIR/"
cp "$PROJECT_DIR/.gitignore" "$DEPLOY_DIR/"
cp "$PROJECT_DIR/docker-compose.yml" "$DEPLOY_DIR/" 2>/dev/null || echo "⚠️  docker-compose.yml no encontrado"
cp "$PROJECT_DIR/CLAUDE.md" "$DEPLOY_DIR/"
cp "$PROJECT_DIR/README.md" "$DEPLOY_DIR/" 2>/dev/null || echo "⚠️  README.md no encontrado"
cp "$PROJECT_DIR/HOSTINGER_MYSQL_SETUP.md" "$DEPLOY_DIR/"
cp "$PROJECT_DIR/deploy-hostinger.sh" "$DEPLOY_DIR/"

# Documentación adicional
mkdir -p "$DEPLOY_DIR/docs"
cp "$PROJECT_DIR/TESTING_GUIDE.md" "$DEPLOY_DIR/docs/" 2>/dev/null || true
cp "$PROJECT_DIR/FRONTEND_GUIDE.md" "$DEPLOY_DIR/docs/" 2>/dev/null || true

# Crear archivo README de instrucciones para MySQL
cat > "$DEPLOY_DIR/INICIO_RAPIDO_MYSQL.md" << 'EOF'
# ⚡ Inicio Rápido: JADSlink en Hostinger (MySQL)

## 📦 1. Subir a Hostinger

```bash
# File Manager: /home/u938946830/
# Upload: jadslink-deploy-mysql.tar.gz
# Click derecho → Extract
```

## 2. Configurar .env

```bash
cd jadslink-deploy
cp api/.env.hostinger .env
nano .env

# Actualizar:
# DATABASE_URL=mysql+aiomysql://usuario:contraseña@localhost:3306/basedatos
```

**Obtén credenciales de**: Panel Hostinger → Bases de Datos

## 3. Instalar & Setup

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Migraciones
alembic upgrade head

# Seed (opcional)
python3 scripts/reset_and_seed.py
```

## 4. Levantar API

```bash
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name jadslink-api
```

## 5. Acceder

```
https://wheat-pigeon-347024.hostingersite.com
Demo: demo@jadslink.com / demo123456
```

---

**Documentación completa**: `HOSTINGER_MYSQL_SETUP.md`
EOF

echo "✅ Archivos copiados"
echo ""

# Mostrar estructura
echo "📊 Estructura del paquete:"
du -sh "$DEPLOY_DIR"
echo "$(find "$DEPLOY_DIR" -type f | wc -l) archivos"
echo ""

# Crear TAR.GZ
echo "📦 Comprimiendo..."
cd "$TEMP_DIR"
tar -czf "$OUTPUT_FILE" jadslink-deploy

# Limpiar temp
rm -rf "$TEMP_DIR"

# Mostrar resultado
if [ -f "$OUTPUT_FILE" ]; then
    SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo ""
    echo "========================================"
    echo "✅ Paquete Creado Exitosamente"
    echo "========================================"
    echo ""
    echo "📍 Ubicación: $OUTPUT_FILE"
    echo "📦 Tamaño: $SIZE"
    echo "🗄️  Base de datos: MySQL/MariaDB"
    echo ""
    echo "📋 Contenido:"
    echo "   - api/              (Backend FastAPI + MySQL)"
    echo "   - dashboard/        (Frontend React)"
    echo "   - agent/            (Field nodes)"
    echo "   - HOSTINGER_MYSQL_SETUP.md"
    echo "   - INICIO_RAPIDO_MYSQL.md"
    echo ""
    echo "🚀 Próximos pasos:"
    echo "   1. Subir a Hostinger"
    echo "   2. Leer HOSTINGER_MYSQL_SETUP.md"
    echo "   3. Ejecutar pasos de configuración"
    echo ""
else
    echo "❌ Error al crear el paquete"
    exit 1
fi
