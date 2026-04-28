#!/bin/bash

# Script para desplegar dashboard compilado a Hostinger

HOSTINGER_HOST="217.65.147.159"
HOSTINGER_PORT="65002"
HOSTINGER_USER="u938946830"
HOSTINGER_PATH="/home/u938946830/domains/wheat-pigeon-347024.hostingersite.com/public_html/dashboard"

DASHBOARD_SOURCE="$(dirname "$0")/dashboard/dist"

if [ ! -d "$DASHBOARD_SOURCE" ]; then
    echo "❌ Error: Dashboard no compilado. Ejecuta primero:"
    echo "   cd dashboard && npm run build"
    exit 1
fi

echo "📦 Desplegando dashboard a Hostinger..."
echo "   Host: $HOSTINGER_HOST"
echo "   Usuario: $HOSTINGER_USER"
echo "   Ruta destino: $HOSTINGER_PATH"
echo ""

# Subir archivos compilados
scp -P $HOSTINGER_PORT -r "$DASHBOARD_SOURCE"/* "$HOSTINGER_USER@$HOSTINGER_HOST:$HOSTINGER_PATH/" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Dashboard desplegado correctamente"
    echo "   Acceso: https://wheat-pigeon-347024.hostingersite.com/dashboard/"
else
    echo "❌ Error al desplegar. Verifica:"
    echo "   - Credenciales SSH correctas"
    echo "   - Conexión a internet"
    echo "   - Ruta de destino existe"
fi
