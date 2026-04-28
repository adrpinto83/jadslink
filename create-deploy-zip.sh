#!/bin/bash

# =============================================================================
# Create Optimized JADSlink Deployment ZIP
# =============================================================================
# Uso: ./create-deploy-zip.sh
# Genera un ZIP optimizado del proyecto para desplegar en Hostinger
# =============================================================================

set -e

echo "========================================"
echo "📦 Creando ZIP para despliegue..."
echo "========================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_ZIP="$PROJECT_DIR/jadslink-deploy.zip"
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
cp "$PROJECT_DIR/.env.production" "$DEPLOY_DIR/"
cp "$PROJECT_DIR/.gitignore" "$DEPLOY_DIR/"
cp "$PROJECT_DIR/docker-compose.yml" "$DEPLOY_DIR/" 2>/dev/null || echo "⚠️  docker-compose.yml no encontrado"
cp "$PROJECT_DIR/CLAUDE.md" "$DEPLOY_DIR/"
cp "$PROJECT_DIR/README.md" "$DEPLOY_DIR/" 2>/dev/null || echo "⚠️  README.md no encontrado"
cp "$PROJECT_DIR/HOSTINGER_SETUP.md" "$DEPLOY_DIR/"

# Scripts importantes
cp "$PROJECT_DIR/deploy-hostinger.sh" "$DEPLOY_DIR/"
cp "$PROJECT_DIR/create-deploy-zip.sh" "$DEPLOY_DIR/" 2>/dev/null || true

# Documentación adicional
mkdir -p "$DEPLOY_DIR/docs"
cp "$PROJECT_DIR/TESTING_GUIDE.md" "$DEPLOY_DIR/docs/" 2>/dev/null || true
cp "$PROJECT_DIR/FRONTEND_GUIDE.md" "$DEPLOY_DIR/docs/" 2>/dev/null || true

# Crear archivo README de instrucciones
cat > "$DEPLOY_DIR/INSTRUCCIONES_DESPLIEGUE.md" << 'EOF'
# 🚀 Instrucciones de Despliegue JADSlink en Hostinger

## 📋 Requisitos Previos

- Acceso SSH al servidor Hostinger
- Python 3.9+
- PostgreSQL disponible en Hostinger
- Almacenamiento: ~500MB

## ⚡ Instalación Rápida (5 minutos)

### 1️⃣ Descargar y Extraer

```bash
# En tu servidor Hostinger
cd /home/u938946830/
unzip jadslink-deploy.zip
cd jadslink-deploy
```

### 2️⃣ Configurar Variables de Entorno

```bash
# Copiar template
cp .env.production .env

# Editar con tus credenciales de Hostinger
nano .env

# Importante: Actualizar estas líneas
# DATABASE_URL=postgresql://tu_usuario:tu_contraseña@localhost:5432/tu_bd
# SECRET_KEY=genera-nueva-clave
# TICKET_HMAC_SECRET=genera-nueva-clave-hmac
```

**Generar claves nuevas:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3️⃣ Ejecutar Script de Despliegue

```bash
chmod +x deploy-hostinger.sh
./deploy-hostinger.sh
```

El script hará automáticamente:
- ✅ Crear virtual environment Python
- ✅ Instalar dependencias
- ✅ Ejecutar migraciones de BD
- ✅ Aplicar seed de datos demo
- ✅ Compilar dashboard React (opcional)

### 4️⃣ Iniciar API

**Opción A: PM2 (Recomendado)**
```bash
npm install -g pm2
cd api
source venv/bin/activate
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name jadslink-api
pm2 save
pm2 startup
```

**Opción B: Systemd**
```bash
# El script deploy-hostinger.sh genera la configuración
# Luego ejecuta:
sudo systemctl enable jadslink-api
sudo systemctl start jadslink-api
```

### 5️⃣ Configurar Nginx (en panel Hostinger)

1. Ve al panel de Hostinger → Administrador de sitios web
2. Crea una entrada para `wheat-pigeon-347024.hostingersite.com`
3. En configuración Nginx, añade:

```nginx
location /api {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location / {
    # Servir el dashboard React
    alias /home/u938946830/jadslink-deploy/dashboard/dist/;
    try_files $uri $uri/ /index.html;
}
```

### 6️⃣ Verificar que Funcione

```bash
# Health check
curl http://localhost:8000/health

# Respuesta esperada:
# {"status":"healthy","checks":{"database":"ok"}}

# Acceder desde navegador:
# https://wheat-pigeon-347024.hostingersite.com
```

## 🔐 Credenciales Demo

Después del seed, usa:

- **Email**: demo@jadslink.com
- **Contraseña**: demo123456

O para superadmin:

- **Email**: admin@jads.com
- **Contraseña**: admin123456

## 🐛 Troubleshooting

### Error: "Cannot connect to database"
```bash
# Verificar credenciales en .env
psql postgresql://usuario:contraseña@localhost:5432/bd_name
```

### Error: "Module not found"
```bash
cd api
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Port 8000 in use"
```bash
# Cambiar puerto en gunicorn
gunicorn -w 4 -b 127.0.0.1:8001 main:app
```

## 📚 Documentación

- `HOSTINGER_SETUP.md` - Guía detallada
- `CLAUDE.md` - Arquitectura del proyecto
- `docs/TESTING_GUIDE.md` - Pruebas

## 🆘 Soporte

- GitHub Issues: [Repo Issues](https://github.com/adrpinto83/jadslink)
- Email: adrpinto83@gmail.com

---

**Status**: Listo para desplegar ✅
**Última actualización**: 2026-04-27
EOF

echo "✅ Archivos copiados"
echo ""

# Mostrar estructura
echo "📊 Estructura del ZIP:"
du -sh "$DEPLOY_DIR"
find "$DEPLOY_DIR" -type f | wc -l
echo " archivos"
echo ""

# Crear TAR.GZ (alternativa a ZIP si zip no está disponible)
echo "📦 Comprimiendo..."
ARCHIVE_FILE="$PROJECT_DIR/jadslink-deploy.tar.gz"
cd "$TEMP_DIR"

if command -v zip &> /dev/null; then
    OUTPUT_ZIP="$PROJECT_DIR/jadslink-deploy.zip"
    zip -r -q "$OUTPUT_ZIP" jadslink-deploy
    FINAL_ARCHIVE="$OUTPUT_ZIP"
else
    tar -czf "$ARCHIVE_FILE" jadslink-deploy
    FINAL_ARCHIVE="$ARCHIVE_FILE"
    echo "⚠️  ZIP no disponible, usando TAR.GZ en su lugar"
fi

# Limpiar temp
rm -rf "$TEMP_DIR"

# Mostrar resultado
if [ -f "$FINAL_ARCHIVE" ]; then
    SIZE=$(du -h "$FINAL_ARCHIVE" | cut -f1)
    ARCHIVE_NAME=$(basename "$FINAL_ARCHIVE")
    echo ""
    echo "========================================"
    echo "✅ Archivo Creado Exitosamente"
    echo "========================================"
    echo ""
    echo "📍 Ubicación: $FINAL_ARCHIVE"
    echo "📦 Tamaño: $SIZE"
    echo "📦 Nombre: $ARCHIVE_NAME"
    echo ""
    echo "📋 Contenido:"
    echo "   - api/                    (Backend FastAPI)"
    echo "   - dashboard/              (Frontend React)"
    echo "   - agent/                  (Field nodes)"
    echo "   - deploy-hostinger.sh     (Script de instalación)"
    echo "   - .env.production         (Template de configuración)"
    echo "   - INSTRUCCIONES_DESPLIEGUE.md"
    echo ""
    echo "⬆️  Próximo paso: Subir a Hostinger"
    echo ""
else
    echo "❌ Error al crear el ZIP"
    exit 1
fi
