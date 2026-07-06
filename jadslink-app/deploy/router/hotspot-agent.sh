#!/bin/sh
# /usr/bin/hotspot-agent.sh
# Agente hotspot - OpenWrt 25.x (uclient-fetch)

CLOUD_URL="${CLOUD_URL:-http://192.168.1.187:8765}"
DEVICE_ID="${DEVICE_ID:-}"
API_KEY="${API_KEY:-}"
INTERVAL="${INTERVAL:-30}"
LOG="/tmp/hotspot-agent.log"
NDS_CODES="/tmp/nds_codes"

log() { echo "[$(date '+%H:%M:%S')] $1" >> "$LOG"; }

http_post() {
  uclient-fetch -q -O - \
    --header="Content-Type: application/json" \
    --header="X-Api-Key: $2" \
    --post-data="$3" \
    "$1" 2>/dev/null
}

SPLASH_PATH="${SPLASH_PATH:-/etc/nodogsplash/htdocs/splash.html}"

update_portal() {
  # Descarga el splash.html ya renderizado (con el branding del operador)
  # desde la nube y lo escribe en NoDogSplash. La nube es la fuente de verdad.
  uclient-fetch -q -T 15 -O /tmp/splash.new \
    "${CLOUD_URL}/api/devices/${DEVICE_ID}/portal/splash" 2>/dev/null
  if [ -s /tmp/splash.new ] && grep -q '\$authaction' /tmp/splash.new; then
    mv /tmp/splash.new "$SPLASH_PATH"
    log "Portal actualizado desde la nube"
  else
    rm -f /tmp/splash.new
    log "update_portal: descarga vacia o invalida, sin cambios"
  fi
}

get_uptime() { awk '{print int($1)}' /proc/uptime 2>/dev/null || echo 0; }

get_cpu() {
  read -r _ u1 n1 s1 i1 _ < /proc/stat
  sleep 1
  read -r _ u2 n2 s2 i2 _ < /proc/stat
  awk "BEGIN{printf \"%.1f\", (($u2+$n2+$s2)-($u1+$n1+$s1))/(($u2+$n2+$s2+$i2)-($u1+$n1+$s1+$i1))*100}" 2>/dev/null || echo 0
}

get_mem_free() {
  awk '/MemFree/{printf "%.1f", $2/1024}' /proc/meminfo 2>/dev/null || echo 0
}

get_wan_ip() {
  ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' || echo ""
}

get_firmware() {
  grep DISTRIB_RELEASE /etc/openwrt_release 2>/dev/null | cut -d= -f2 | tr -d '"' || echo ""
}

get_clients_json() {
  # NoDogSplash 5.x json: { "clients": { "<mac>": { "ip", "mac", "state",
  # "downloaded", "uploaded", ... } } }. Campos por linea, sin espacios tras ':'.
  # Solo reportamos clientes con state == Authenticated.
  # /tmp/nds_sessions (MAC|CODE) registra que codigo uso cada cliente activo.
  NDS=$(ndsctl json 2>/dev/null)
  [ -z "$NDS" ] && echo "[]" && return
  echo "$NDS" | awk -v sess="/tmp/nds_sessions" '
  BEGIN{
    print "["; sep=""
    while ((getline line < sess) > 0) {
      n = split(line, a, "|")
      if (n >= 2) codes[a[1]] = a[2]
    }
  }
  /"mac":/{mac=$0; sub(/^[^:]*:"/,"",mac); sub(/".*/,"",mac)}
  /"ip":/{ip=$0; sub(/^[^:]*:"/,"",ip); sub(/".*/,"",ip)}
  /"state":/{st=$0; sub(/^[^:]*:"/,"",st); sub(/".*/,"",st)}
  /"downloaded":/{dn=$0; sub(/^[^:]*:/,"",dn); sub(/[^0-9].*/,"",dn)}
  /"uploaded":/{up=$0; sub(/^[^:]*:/,"",up); sub(/[^0-9].*/,"",up);
    if(st=="Authenticated"){
      code = (mac in codes) ? codes[mac] : ""
      printf "%s{\"mac\":\"%s\",\"ip\":\"%s\",\"bytes_in\":%s,\"bytes_out\":%s,\"code_used\":\"%s\"}",sep,mac,ip,dn,up,code
      sep=","
    }
  }
  END{print "]"}' 2>/dev/null || echo "[]"
}

send_heartbeat() {
  CLIENTS=$(get_clients_json)
  COUNT=$(echo "$CLIENTS" | grep -o '"mac"' | wc -l | tr -d ' ')

  FW=$(get_firmware)
  WAN=$(get_wan_ip)
  CPU=$(get_cpu)
  MEM=$(get_mem_free)
  UP=$(get_uptime)

  PAYLOAD="{\"firmware\":\"$FW\",\"wan_ip\":\"$WAN\",\"clients_count\":${COUNT:-0},\"bytes_in\":0,\"bytes_out\":0,\"cpu_load\":$CPU,\"mem_free_mb\":$MEM,\"uptime_sec\":$UP,\"clients\":$CLIENTS}"

  RESPONSE=$(http_post "${CLOUD_URL}/api/devices/${DEVICE_ID}/heartbeat" "$API_KEY" "$PAYLOAD")

  if [ -n "$RESPONSE" ]; then
    log "Heartbeat OK"
    process_commands "$RESPONSE"
  else
    log "Heartbeat fallido - sin respuesta"
  fi
}

process_commands() {
  RESP="$1"
  echo "$RESP" | grep -o '"action":"[^"]*"' | cut -d'"' -f4 | while read -r ACTION; do
    log "Comando: $ACTION"
    case "$ACTION" in
      reboot)
        http_post "${CLOUD_URL}/api/devices/${DEVICE_ID}/command-result" "$API_KEY" \
          '{"command_id":0,"status":"done","result":"rebooting"}' >/dev/null
        sleep 2; reboot
        ;;
      add_codes)
        DUR_MIN=$(echo "$RESP" | grep -o '"duration_min":[0-9]*' | head -1 | cut -d: -f2)
        DUR_SEC=$(( ${DUR_MIN:-60} * 60 ))
        BW_DN=$(echo "$RESP" | grep -o '"bandwidth_dn":[0-9]*' | head -1 | cut -d: -f2)
        BW_UP=$(echo "$RESP" | grep -o '"bandwidth_up":[0-9]*' | head -1 | cut -d: -f2)
        EXP=$(echo "$RESP" | grep -o '"expires_at":[0-9]*' | head -1 | cut -d: -f2)
        COUNT=0
        BLOCK=$(echo "$RESP" | grep -o '"codes":\[[^]]*\]' | grep -o '"[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]*"' | tr -d '"')
        for CODE in $BLOCK; do
          grep -q "^${CODE}|" "$NDS_CODES" 2>/dev/null || \
            printf '%s\n' "${CODE}|${DUR_SEC}|${BW_DN:-0}|${BW_UP:-0}|${EXP:-0}" >> "$NDS_CODES"
          COUNT=$((COUNT+1))
        done
        log "add_codes: $COUNT codigos en cache (expira_epoch=${EXP:-0})"
        ;;
      revoke_code)
        CODE=$(echo "$RESP" | grep -o '"code":"[^"]*"' | head -1 | cut -d'"' -f4)
        [ -n "$CODE" ] && sed -i "/^${CODE}|/d" "$NDS_CODES" && log "Codigo $CODE revocado"
        ;;
      update_config)
        # El branding del portal vive en la config; basta con re-descargar el
        # splash renderizado desde la nube.
        update_portal
        ;;
      set_ssid)
        SSID=$(echo "$RESP" | grep -o '"ssid":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -z "$SSID" ]; then
          log "set_ssid: SSID vacío, ignorado"
        else
          for IFACE in $(uci show wireless | grep '\.ssid=' | cut -d= -f1 | sed 's/\.ssid$//'); do
            uci set "${IFACE}.ssid=${SSID}"
          done
          uci commit wireless && wifi reload
          log "SSID cambiado a: $SSID"
        fi
        ;;
      *) log "Comando no implementado: $ACTION" ;;
    esac
  done
}

validate_code() {
  CODE="$1"; MAC="$2"; IP="$3"
  if grep -q "^${CODE}|" "$NDS_CODES" 2>/dev/null; then
    LINE=$(grep "^${CODE}|" "$NDS_CODES" | head -1)
    DUR=$(echo "$LINE" | cut -d'|' -f2)
    BW_DN=$(echo "$LINE" | cut -d'|' -f3)
    BW_UP=$(echo "$LINE" | cut -d'|' -f4)
    ndsctl auth "$MAC" "$DUR" "$BW_DN" "$BW_UP" >/dev/null 2>&1
    sed -i "/^${CODE}|/d" "$NDS_CODES"
    log "Codigo $CODE usado por $MAC ($IP)"
    echo ok
  else
    log "Codigo $CODE invalido para $MAC"
    echo invalid
  fi
}

[ -f /etc/hotspot/agent.conf ] && . /etc/hotspot/agent.conf

if [ -z "$DEVICE_ID" ] || [ -z "$API_KEY" ]; then
  log "ERROR: DEVICE_ID y API_KEY no configurados en /etc/hotspot/agent.conf"
  exit 1
fi

case "$1" in
  validate) validate_code "$2" "$3" "$4" ;;
  once)     send_heartbeat ;;
  portal)   update_portal ;;
  *)
    log "Agente iniciado. Intervalo: ${INTERVAL}s"
    update_portal   # aplica branding actual al arrancar
    while true; do
      send_heartbeat
      sleep "$INTERVAL"
    done
    ;;
esac

