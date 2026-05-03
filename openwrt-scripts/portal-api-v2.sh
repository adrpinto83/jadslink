#!/bin/sh
#
# JADSlink Portal API v2
# Maneja activación de códigos con validación de una sola uso
# Gestiona sesiones con timeout automático
#
# Usage: Llamado como CGI por uhttpd
# POST: action=activate&code=ABC123XYZ&client_ip=192.168.1.207
#

# Directorios de configuración
CACHE_DIR="/var/cache/jadslink"
LOG_DIR="/var/log/jadslink"
CODES_FILE="$CACHE_DIR/demo_tickets.db"
USED_CODES_FILE="$CACHE_DIR/used_codes.db"
SESSIONS_FILE="$CACHE_DIR/sessions.db"
SESSION_LOG="$LOG_DIR/sessions.log"
USED_LOG="$LOG_DIR/used_codes.log"

# Crear directorios si no existen
mkdir -p "$CACHE_DIR" "$LOG_DIR"

# Crear archivos si no existen
[ ! -f "$CODES_FILE" ] && touch "$CODES_FILE"
[ ! -f "$USED_CODES_FILE" ] && touch "$USED_CODES_FILE"
[ ! -f "$SESSIONS_FILE" ] && touch "$SESSIONS_FILE"

# Función para enviar respuesta JSON
json_response() {
    echo "Content-Type: application/json"
    echo ""
    echo "$1"
}

# Función para registrar sesión
log_session() {
    local session_id="$1"
    local client_ip="$2"
    local code="$3"
    local duration="$4"
    local timestamp=$(date +%s)

    # Guardar en sessions.db: SESSION_ID:IP:CODE:TIMESTAMP:DURATION:STATUS
    echo "$session_id:$client_ip:$code:$timestamp:$duration:active" >> "$SESSIONS_FILE"

    # Guardar en log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Session=$session_id IP=$client_ip Code=$code Duration=$duration" >> "$SESSION_LOG"
}

# Función para registrar código usado
log_used_code() {
    local code="$1"
    local client_ip="$2"
    local timestamp=$(date +%s)

    # Guardar en used_codes.db: CODE:IP:TIMESTAMP
    echo "$code:$client_ip:$timestamp" >> "$USED_CODES_FILE"

    # Guardar en log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Code=$code UsedBy=$client_ip" >> "$USED_LOG"
}

# Función para añadir regla de firewall
add_firewall_rule() {
    local client_ip="$1"

    # Añadir regla nftables para permitir este IP
    # La regla permite tráfico desde este IP hacia WAN (cualquier cosa excepto LAN 192.168.1.0/24)
    nft insert rule inet jadslink forward ip saddr "$client_ip" ip daddr != 192.168.1.0/24 counter accept 2>/dev/null || true

    return 0
}

# Función para generar session ID
generate_session_id() {
    # Usar combinación de IP, código y timestamp para generar session ID único
    local client_ip="$1"
    local code="$2"
    local timestamp=$(date +%s%N)

    # Crear hash: primeros 16 caracteres de hash md5
    echo "$client_ip:$code:$timestamp" | md5sum | cut -c1-16
}

# ============================================
# MAIN
# ============================================

# Leer POST data
read POST_DATA

# Parsear parámetros
action=$(echo "$POST_DATA" | grep -o 'action=[^&]*' | cut -d= -f2 | head -1)
code=$(echo "$POST_DATA" | grep -o 'code=[^&]*' | cut -d= -f2 | head -1 | tr -d '\r')
client_ip=$(echo "$POST_DATA" | grep -o 'client_ip=[^&]*' | cut -d= -f2 | head -1)

# Si client_ip no viene en POST, usar REMOTE_ADDR como fallback
if [ -z "$client_ip" ]; then
    client_ip="$REMOTE_ADDR"
fi

# Validar action
if [ "$action" != "activate" ]; then
    json_response '{"success": false, "message": "Acción inválida"}'
    exit 0
fi

# Validar code
if [ -z "$code" ]; then
    json_response '{"success": false, "message": "Código no proporcionado"}'
    exit 0
fi

# Validar client_ip
if [ -z "$client_ip" ]; then
    json_response '{"success": false, "message": "No se pudo detectar dirección IP del cliente"}'
    exit 0
fi

# ============================================
# VERIFICACIÓN 1: ¿Ya fue usado este código?
# ============================================
if grep -q "^$code:" "$USED_CODES_FILE" 2>/dev/null; then
    # El código ya fue usado
    json_response '{"success": false, "message": "Código ya fue utilizado y expiró"}'
    exit 0
fi

# ============================================
# VERIFICACIÓN 2: ¿Este IP ya está autenticado?
# ============================================
if grep -q "^[^:]*:$client_ip:" "$SESSIONS_FILE" 2>/dev/null; then
    # Este IP ya tiene una sesión activa
    # Verificar si aún está dentro del tiempo de validez
    existing_session=$(grep "^[^:]*:$client_ip:" "$SESSIONS_FILE" | tail -1)

    # Si encontramos una sesión activa, devolver error
    if echo "$existing_session" | grep -q ":active$"; then
        json_response '{"success": false, "message": "Este dispositivo ya tiene una sesión activa"}'
        exit 0
    fi
fi

# ============================================
# VERIFICACIÓN 3: ¿El código existe?
# ============================================
if ! grep -q "^$code:" "$CODES_FILE" 2>/dev/null; then
    json_response '{"success": false, "message": "Código no válido o servidor no disponible"}'
    exit 0
fi

# ============================================
# ÉXITO: Extraer duración
# ============================================
DURATION=$(grep "^$code:" "$CODES_FILE" | cut -d: -f2)

# Generar session ID
SESSION_ID=$(generate_session_id "$client_ip" "$code")

# ============================================
# ACCIONES POST-VALIDACIÓN
# ============================================

# 1. Marcar código como usado (eliminarlo del archivo de códigos disponibles)
sed -i "/^$code:/d" "$CODES_FILE" 2>/dev/null || true

# 2. Registrar código como usado
log_used_code "$code" "$client_ip"

# 3. Crear sesión
log_session "$SESSION_ID" "$client_ip" "$code" "$DURATION"

# 4. Añadir regla de firewall para este IP
add_firewall_rule "$client_ip"

# 5. Devolver respuesta exitosa
json_response '{"success": true, "message": "✓ Activado. Tienes acceso por '$DURATION' minutos.", "session_id": "'$SESSION_ID'", "expires_in": '$((DURATION * 60))'}'

exit 0
