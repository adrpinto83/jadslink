#!/bin/bash
#
# JADSlink FASE 2.2 v2 — Script de Deployment Automático
# Copiar COMPLETAMENTE este script y pegarlo en la consola de OpenWrt
#
# Uso:
# 1. SSH a OpenWrt: ssh root@192.168.0.10
# 2. Copiar TODO el contenido de este script
# 3. Pegar en la consola OpenWrt
# 4. Presionar Enter
# 5. Esperar a que termine (2-3 minutos)
#

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║     JADSlink FASE 2.2 v2 — Deployment Automático            ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ============================================
# PASO 1: Crear Directorios
# ============================================
echo "[1/5] Creando directorios..."

mkdir -p /www/cgi-bin
mkdir -p /usr/local/bin
mkdir -p /etc/init.d
mkdir -p /var/cache/jadslink
mkdir -p /var/log/jadslink

echo "✓ Directorios creados"

# ============================================
# PASO 2: Copiar Scripts
# ============================================
echo ""
echo "[2/5] Copiando scripts..."

# portal-api-v2.sh (CGI script)
cat > /www/cgi-bin/portal-api-v2.sh << 'SCRIPT_CGI_EOF'
#!/bin/sh
#
# JADSlink Portal API v2
# Maneja activación de códigos con validación de una sola uso
#

CACHE_DIR="/var/cache/jadslink"
LOG_DIR="/var/log/jadslink"
CODES_FILE="$CACHE_DIR/demo_tickets.db"
USED_CODES_FILE="$CACHE_DIR/used_codes.db"
SESSIONS_FILE="$CACHE_DIR/sessions.db"
SESSION_LOG="$LOG_DIR/sessions.log"
USED_LOG="$LOG_DIR/used_codes.log"

mkdir -p "$CACHE_DIR" "$LOG_DIR"
[ ! -f "$CODES_FILE" ] && touch "$CODES_FILE"
[ ! -f "$USED_CODES_FILE" ] && touch "$USED_CODES_FILE"
[ ! -f "$SESSIONS_FILE" ] && touch "$SESSIONS_FILE"

json_response() {
    echo "Content-Type: application/json"
    echo ""
    echo "$1"
}

log_session() {
    local session_id="$1"
    local client_ip="$2"
    local code="$3"
    local duration="$4"
    local timestamp=$(date +%s)

    echo "$session_id:$client_ip:$code:$timestamp:$duration:active" >> "$SESSIONS_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Session=$session_id IP=$client_ip Code=$code Duration=$duration" >> "$SESSION_LOG"
}

log_used_code() {
    local code="$1"
    local client_ip="$2"
    local timestamp=$(date +%s)

    echo "$code:$client_ip:$timestamp" >> "$USED_CODES_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Code=$code UsedBy=$client_ip" >> "$USED_LOG"
}

add_firewall_rule() {
    local client_ip="$1"
    nft insert rule inet jadslink forward ip saddr "$client_ip" ip daddr != 192.168.1.0/24 counter accept 2>/dev/null || true
    return 0
}

generate_session_id() {
    local client_ip="$1"
    local code="$2"
    local timestamp=$(date +%s%N)
    echo "$client_ip:$code:$timestamp" | md5sum | cut -c1-16
}

read POST_DATA

action=$(echo "$POST_DATA" | grep -o 'action=[^&]*' | cut -d= -f2 | head -1)
code=$(echo "$POST_DATA" | grep -o 'code=[^&]*' | cut -d= -f2 | head -1 | tr -d '\r')
client_ip=$(echo "$POST_DATA" | grep -o 'client_ip=[^&]*' | cut -d= -f2 | head -1)

if [ -z "$client_ip" ]; then
    client_ip="$REMOTE_ADDR"
fi

if [ "$action" != "activate" ]; then
    json_response '{"success": false, "message": "Acción inválida"}'
    exit 0
fi

if [ -z "$code" ]; then
    json_response '{"success": false, "message": "Código no proporcionado"}'
    exit 0
fi

if [ -z "$client_ip" ]; then
    json_response '{"success": false, "message": "No se pudo detectar dirección IP"}'
    exit 0
fi

if grep -q "^$code:" "$USED_CODES_FILE" 2>/dev/null; then
    json_response '{"success": false, "message": "Código ya fue utilizado y expiró"}'
    exit 0
fi

if grep -q "^[^:]*:$client_ip:" "$SESSIONS_FILE" 2>/dev/null; then
    existing_session=$(grep "^[^:]*:$client_ip:" "$SESSIONS_FILE" | tail -1)
    if echo "$existing_session" | grep -q ":active$"; then
        json_response '{"success": false, "message": "Este dispositivo ya tiene una sesión activa"}'
        exit 0
    fi
fi

if ! grep -q "^$code:" "$CODES_FILE" 2>/dev/null; then
    json_response '{"success": false, "message": "Código no válido o servidor no disponible"}'
    exit 0
fi

DURATION=$(grep "^$code:" "$CODES_FILE" | cut -d: -f2)
SESSION_ID=$(generate_session_id "$client_ip" "$code")

sed -i "/^$code:/d" "$CODES_FILE" 2>/dev/null || true
log_used_code "$code" "$client_ip"
log_session "$SESSION_ID" "$client_ip" "$code" "$DURATION"
add_firewall_rule "$client_ip"

json_response '{"success": true, "message": "✓ Activado. Tienes acceso por '$DURATION' minutos.", "session_id": "'$SESSION_ID'", "expires_in": '$((DURATION * 60))'}'

exit 0
SCRIPT_CGI_EOF

echo "✓ portal-api-v2.sh copiado"

# session-cleanup.sh
cat > /usr/local/bin/session-cleanup.sh << 'SCRIPT_CLEANUP_EOF'
#!/bin/sh
#
# JADSlink Session Cleanup & Expiration
#

SESSIONS_FILE="/var/cache/jadslink/sessions.db"
SESSION_LOG="/var/log/jadslink/sessions.log"
EXPIRED_LOG="/var/log/jadslink/expired_sessions.log"

mkdir -p /var/cache/jadslink /var/log/jadslink

remove_firewall_rule() {
    local client_ip="$1"
    nft list table inet jadslink --handle 2>/dev/null | grep "ip saddr $client_ip" | while read -r line; do
        handle=$(echo "$line" | grep -o 'handle [0-9]*' | cut -d' ' -f2 | tail -1)
        if [ -n "$handle" ]; then
            nft delete rule inet jadslink forward handle "$handle" 2>/dev/null || true
        fi
    done
    return 0
}

log_expired_session() {
    local session_id="$1"
    local client_ip="$2"
    local code="$3"
    local duration="$4"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ExpiredSession=$session_id IP=$client_ip Code=$code Duration=$duration" >> "$EXPIRED_LOG"
}

[ ! -f "$SESSIONS_FILE" ] && exit 0

current_timestamp=$(date +%s)

while IFS=: read -r session_id client_ip code created_at duration status; do
    [ -z "$session_id" ] && continue

    elapsed=$((current_timestamp - created_at))
    session_duration=$((duration * 60))

    if [ "$elapsed" -ge "$session_duration" ] && [ "$status" = "active" ]; then
        temp_file="${SESSIONS_FILE}.tmp"
        > "$temp_file"

        while IFS=: read -r sid cip c cat d stat; do
            if [ "$sid" = "$session_id" ]; then
                echo "$sid:$cip:$c:$cat:$d:expired" >> "$temp_file"
            else
                echo "$sid:$cip:$c:$cat:$d:$stat" >> "$temp_file"
            fi
        done < "$SESSIONS_FILE"

        mv "$temp_file" "$SESSIONS_FILE"
        remove_firewall_rule "$client_ip"
        log_expired_session "$session_id" "$client_ip" "$code" "$duration"
    fi

done < "$SESSIONS_FILE"

exit 0
SCRIPT_CLEANUP_EOF

echo "✓ session-cleanup.sh copiado"

# jadslink-firewall-v2.sh
cat > /usr/local/bin/jadslink-firewall-v2.sh << 'SCRIPT_FIREWALL_EOF'
#!/bin/sh
#
# JADSlink Firewall Configuration v2
#

LAN_SUBNET="192.168.1.0/24"
ROUTER_IP="192.168.1.1"

nft list table inet jadslink > /dev/null 2>&1 || {
    nft add table inet jadslink
}

nft list chain inet jadslink prerouting > /dev/null 2>&1 || {
    nft add chain inet jadslink prerouting '{ type nat hook prerouting priority dstnat + 1 ; policy accept ; }'
}

nft list chain inet jadslink prerouting | grep -q "udp dport 53 accept" || {
    nft add rule inet jadslink prerouting udp dport 53 accept
}

nft list chain inet jadslink postrouting > /dev/null 2>&1 || {
    nft add chain inet jadslink postrouting '{ type nat hook postrouting priority srcnat + 1 ; policy accept ; }'
}

nft list chain inet jadslink postrouting | grep -q "masquerade" || {
    nft add rule inet jadslink postrouting ip saddr "$LAN_SUBNET" ip daddr != "$LAN_SUBNET" counter masquerade
}

nft list chain inet jadslink forward > /dev/null 2>&1 || {
    nft add chain inet jadslink forward '{ type filter hook forward priority filter + 1 ; policy accept ; }'
}

nft list chain inet jadslink forward | grep -q "established,related accept" || {
    nft add rule inet jadslink forward ct state established,related counter accept
}

nft list chain inet jadslink forward | grep -q "ip daddr $ROUTER_IP counter accept" || {
    nft add rule inet jadslink forward ip daddr "$ROUTER_IP" counter accept
}

nft list chain inet jadslink forward | grep -q "ip daddr $LAN_SUBNET counter accept" || {
    nft add rule inet jadslink forward ip daddr "$LAN_SUBNET" counter accept
}

nft list chain inet jadslink forward | grep -q "BLOCK_UNAUTH" || {
    nft add rule inet jadslink forward ip saddr "$LAN_SUBNET" ip daddr != "$LAN_SUBNET" counter drop comment "BLOCK_UNAUTH"
}

echo "✓ Firewall initialized: Default-DENY policy configured"
SCRIPT_FIREWALL_EOF

echo "✓ jadslink-firewall-v2.sh copiado"

# jadslink-session-cleanup.init
cat > /etc/init.d/jadslink-session-cleanup << 'SCRIPT_INIT_EOF'
#!/bin/sh /etc/rc.common
#
# JADSlink Session Cleanup Service
#

START=91
STOP=10

USE_PROCD=1
CLEANUP_SCRIPT="/usr/local/bin/session-cleanup.sh"
CLEANUP_INTERVAL=60

start_service() {
    procd_open_instance "jadslink-session-cleanup"
    procd_set_param command /bin/sh -c "
    while true; do
        $CLEANUP_SCRIPT 2>> /var/log/jadslink/cleanup.log
        sleep $CLEANUP_INTERVAL
    done
    "
    procd_set_param respawn 3600 5 0
    procd_close_instance
}

stop_service() {
    return 0
}

reload_service() {
    stop_service
    start_service
}
SCRIPT_INIT_EOF

echo "✓ jadslink-session-cleanup.init copiado"

# ============================================
# PASO 3: Dar Permisos de Ejecución
# ============================================
echo ""
echo "[3/5] Dando permisos de ejecución..."

chmod 755 /www/cgi-bin/portal-api-v2.sh
chmod 755 /usr/local/bin/session-cleanup.sh
chmod 755 /usr/local/bin/jadslink-firewall-v2.sh
chmod 755 /etc/init.d/jadslink-session-cleanup

echo "✓ Permisos configurados"

# ============================================
# PASO 4: Inicializar Servicios
# ============================================
echo ""
echo "[4/5] Inicializando servicios..."

# Firewall
/usr/local/bin/jadslink-firewall-v2.sh
echo "✓ Firewall inicializado"

# Session cleanup service
/etc/init.d/jadslink-session-cleanup start
/etc/init.d/jadslink-session-cleanup enable
echo "✓ Session cleanup service iniciado"

# ============================================
# PASO 5: Crear Códigos de Demostración
# ============================================
echo ""
echo "[5/5] Creando códigos de demostración..."

cat > /var/cache/jadslink/demo_tickets.db << 'CODES_EOF'
ABC123XYZ:30
DEF456UVW:60
GHI789RST:1440
TEST001:30
TEST002:60
TEST003:1440
TICKET001:30
TICKET002:60
TICKET003:1440
CODES_EOF

chmod 644 /var/cache/jadslink/demo_tickets.db
echo "✓ Códigos de demostración creados"

# ============================================
# VERIFICACIÓN
# ============================================
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "VERIFICACIÓN DEL DEPLOYMENT:"
echo ""

echo "1. Firewall:"
if nft list table inet jadslink > /dev/null 2>&1; then
    echo "   ✓ Tabla nftables 'inet jadslink' EXISTS"
else
    echo "   ✗ Tabla nftables NO existe"
fi

echo ""
echo "2. Session cleanup service:"
if ps aux | grep -q "[s]ession-cleanup.sh"; then
    echo "   ✓ Session cleanup está CORRIENDO"
else
    echo "   ✗ Session cleanup NO está corriendo"
fi

echo ""
echo "3. Portal CGI:"
if [ -f /www/cgi-bin/portal-api-v2.sh ] && [ -x /www/cgi-bin/portal-api-v2.sh ]; then
    echo "   ✓ portal-api-v2.sh EXISTS y es EXECUTABLE"
else
    echo "   ✗ portal-api-v2.sh tiene PROBLEMAS"
fi

echo ""
echo "4. Códigos de demostración:"
if [ -f /var/cache/jadslink/demo_tickets.db ]; then
    count=$(wc -l < /var/cache/jadslink/demo_tickets.db)
    echo "   ✓ demo_tickets.db EXISTS con $count códigos"
else
    echo "   ✗ demo_tickets.db NO existe"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "✅ DEPLOYMENT COMPLETADO EXITOSAMENTE"
echo ""
echo "Próximos pasos:"
echo "1. Conecta cliente a WiFi: JADSlink-Hotspot"
echo "2. Abre navegador: http://google.com"
echo "3. Deberías ver el portal automáticamente"
echo "4. Ingresa código: ABC123XYZ"
echo "5. Presiona Activar"
echo ""
echo "Para más detalles, consulta:"
echo "  - DEPLOYMENT_OPENWRT_V2.md"
echo "  - FASE_2_2_FINAL_REQUIREMENTS_VALIDATION.md"
echo ""
