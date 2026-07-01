#!/bin/sh
# /usr/bin/jadslink-auth.sh
# nodogsplash 5.x binauth: exit 0 + stdout=SEGUNDOS de sesion para aceptar, exit 1 para rechazar
# NOTA: el contrato de binauth de NoDogSplash lee el stdout en SEGUNDOS (no minutos).
#       La config UCI (sessiontimeout, etc.) sigue siendo en minutos: son escalas distintas.

ACTION="$1"
MAC="$2"
USERNAME="$3"
PASSWORD="$4"

NDS_CODES="/tmp/nds_codes"
NDS_SESSIONS="/tmp/nds_sessions"   # MAC|CODE — que codigo uso cada cliente activo
CONF="/etc/hotspot/agent.conf"
LOG="/tmp/hotspot-agent.log"
SESSION_JS="/etc/nodogsplash/htdocs/session.js"  # connected.html lee de aqui los minutos

log() { echo "[$(date '+%H:%M:%S')] BINAUTH: $1" >> "$LOG"; }

# Deja en session.js los minutos otorgados para que la pantalla de "Conectado"
# muestre la duracion real del codigo (no un valor fijo).
write_session_js() {
  MINS=$(( ${1:-0} / 60 ))
  [ "$MINS" -lt 1 ] && MINS=1
  echo "window.JADS_MINS=${MINS};" > "$SESSION_JS" 2>/dev/null
}

[ -f "$CONF" ] && . "$CONF"

case "$ACTION" in
  auth_client)
    CODE=$(echo "$USERNAME" | tr 'a-z' 'A-Z' | sed 's/ //g')
    log "Validando codigo '$CODE' para MAC $MAC"

    if [ -z "$CODE" ]; then
      log "Codigo vacio - rechazado"
      exit 1
    fi

    # 1. Cache local /tmp/nds_codes (formato: CODIGO|segundos|bw_dn|bw_up|expira_epoch)
    if [ -f "$NDS_CODES" ] && grep -q "^${CODE}|" "$NDS_CODES" 2>/dev/null; then
      LINE=$(grep "^${CODE}|" "$NDS_CODES" | head -1)
      DUR_SEC=$(echo "$LINE" | cut -d'|' -f2)
      EXP=$(echo "$LINE" | cut -d'|' -f5)
      [ "${DUR_SEC:-0}" -lt 60 ] 2>/dev/null && DUR_SEC=3600
      # Vencimiento: si el codigo tiene fecha de expiracion y ya paso, rechazar
      NOW=$(date +%s)
      if [ "${EXP:-0}" -gt 0 ] 2>/dev/null && [ "$NOW" -gt "$EXP" ] 2>/dev/null; then
        sed -i "/^${CODE}|/d" "$NDS_CODES"
        log "Codigo $CODE expirado (local) para $MAC"
        exit 1
      fi
      sed -i "/^${CODE}|/d" "$NDS_CODES"
      # Registrar que esta MAC uso este codigo
      sed -i "/^${MAC}|/d" "$NDS_SESSIONS" 2>/dev/null
      printf '%s\n' "${MAC}|${CODE}" >> "$NDS_SESSIONS"
      write_session_js "$DUR_SEC"
      log "Codigo $CODE valido (local) - ${DUR_SEC}s para $MAC"
      echo "$DUR_SEC"
      exit 0
    fi

    # 2. Cloud API
    if [ -n "$CLOUD_URL" ] && [ -n "$DEVICE_ID" ] && [ -n "$API_KEY" ]; then
      PAYLOAD="{\"code\":\"$CODE\",\"mac\":\"$MAC\"}"
      RESULT=$(uclient-fetch -q -O - \
        --header="Content-Type: application/json" \
        --header="X-Api-Key: $API_KEY" \
        --post-data="$PAYLOAD" \
        "${CLOUD_URL}/api/devices/${DEVICE_ID}/codes/validate" 2>/dev/null)

      if echo "$RESULT" | grep -q '"valid":true'; then
        DUR_SEC=$(echo "$RESULT" | grep -o '"duration":[0-9]*' | cut -d: -f2)
        [ "${DUR_SEC:-0}" -lt 60 ] 2>/dev/null && DUR_SEC=3600
        # Registrar que esta MAC uso este codigo
        sed -i "/^${MAC}|/d" "$NDS_SESSIONS" 2>/dev/null
        printf '%s\n' "${MAC}|${CODE}" >> "$NDS_SESSIONS"
        write_session_js "$DUR_SEC"
        log "Codigo $CODE valido (cloud) - ${DUR_SEC}s para $MAC"
        echo "$DUR_SEC"
        exit 0
      fi
    fi

    log "Codigo $CODE invalido para $MAC"
    exit 1
    ;;

  client_deauth|idle_deauth|timeout_deauth|ndsctl_deauth|shutdown_deauth)
    log "Evento $ACTION: MAC=$MAC"
    sed -i "/^${MAC}|/d" "$NDS_SESSIONS" 2>/dev/null
    ;;

  client_auth)
    log "Evento $ACTION: MAC=$MAC"
    ;;
esac

exit 0
