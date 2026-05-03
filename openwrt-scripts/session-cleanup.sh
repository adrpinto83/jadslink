#!/bin/sh
#
# JADSlink Session Cleanup & Expiration
# Ejecutado periódicamente (ej: cada 60 segundos) para:
# - Expirar sesiones vencidas
# - Remover reglas de firewall
# - Actualizar estado de sesiones
#
# Llamar como: /etc/init.d/jadslink-session-cleanup
#

SESSIONS_FILE="/var/cache/jadslink/sessions.db"
SESSION_LOG="/var/log/jadslink/sessions.log"
EXPIRED_LOG="/var/log/jadslink/expired_sessions.log"

# Crear directorios si no existen
mkdir -p /var/cache/jadslink /var/log/jadslink

# Función para remover regla de firewall
remove_firewall_rule() {
    local client_ip="$1"

    # Obtener handles de las reglas para este IP y removerlas
    nft list table inet jadslink --handle | grep "ip saddr $client_ip" | while read -r line; do
        # Extraer el handle (última número en la línea)
        handle=$(echo "$line" | grep -o 'handle [0-9]*' | cut -d' ' -f2 | tail -1)

        if [ -n "$handle" ]; then
            nft delete rule inet jadslink forward handle "$handle" 2>/dev/null || true
        fi
    done

    return 0
}

# Función para registrar sesión expirada
log_expired_session() {
    local session_id="$1"
    local client_ip="$2"
    local code="$3"
    local duration="$4"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ExpiredSession=$session_id IP=$client_ip Code=$code Duration=$duration" >> "$EXPIRED_LOG"
}

# ============================================
# MAIN
# ============================================

# Si el archivo de sesiones no existe, salir
[ ! -f "$SESSIONS_FILE" ] && exit 0

current_timestamp=$(date +%s)

# Procesar cada sesión
while IFS=: read -r session_id client_ip code created_at duration status; do
    # Saltar líneas vacías
    [ -z "$session_id" ] && continue

    # Calcular tiempo desde que se creó la sesión
    elapsed=$((current_timestamp - created_at))
    session_duration=$((duration * 60))  # Convertir minutos a segundos

    # Si la sesión expiró
    if [ "$elapsed" -ge "$session_duration" ] && [ "$status" = "active" ]; then
        # Marcar como expirada
        # Crear archivo temporal con sesiones actualizadas
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

        # Remover regla de firewall
        remove_firewall_rule "$client_ip"

        # Registrar expiración
        log_expired_session "$session_id" "$client_ip" "$code" "$duration"
    fi

done < "$SESSIONS_FILE"

exit 0
