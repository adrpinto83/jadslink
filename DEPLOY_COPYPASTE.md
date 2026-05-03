# 🚀 DEPLOYMENT COPY-PASTE — Ejecutar directamente en OpenWrt

**Método**: Copy-paste línea por línea en consola OpenWrt
**Tiempo**: 10 minutos
**Dificultad**: Muy baja

---

## 📋 Paso 1: Conectar a OpenWrt por SSH

Desde tu máquina:
```bash
ssh root@192.168.0.10
# Password: 123456
```

Deberías ver:
```
root@OpenWrt:~#
```

---

## 🔧 Paso 2: Crear Directorios

**Copia-pega esto en OpenWrt:**

```bash
mkdir -p /www/cgi-bin /usr/local/bin /etc/init.d /var/cache/jadslink /var/log/jadslink && echo "✓ Directorios creados"
```

---

## 📝 Paso 3: Copiar portal-api-v2.sh

**Copia-pega COMPLETO en OpenWrt:**

```bash
cat > /www/cgi-bin/portal-api-v2.sh << 'PORTAL_EOF'
#!/bin/sh
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
[ -z "$client_ip" ] && client_ip="$REMOTE_ADDR"

[ "$action" != "activate" ] && { json_response '{"success": false, "message": "Acción inválida"}'; exit 0; }
[ -z "$code" ] && { json_response '{"success": false, "message": "Código no proporcionado"}'; exit 0; }
[ -z "$client_ip" ] && { json_response '{"success": false, "message": "No se pudo detectar IP"}'; exit 0; }

grep -q "^$code:" "$USED_CODES_FILE" 2>/dev/null && { json_response '{"success": false, "message": "Código ya fue utilizado y expiró"}'; exit 0; }

grep -q "^[^:]*:$client_ip:" "$SESSIONS_FILE" 2>/dev/null && {
    existing_session=$(grep "^[^:]*:$client_ip:" "$SESSIONS_FILE" | tail -1)
    echo "$existing_session" | grep -q ":active$" && { json_response '{"success": false, "message": "Este dispositivo ya tiene una sesión activa"}'; exit 0; }
}

grep -q "^$code:" "$CODES_FILE" 2>/dev/null || { json_response '{"success": false, "message": "Código no válido"}'; exit 0; }

DURATION=$(grep "^$code:" "$CODES_FILE" | cut -d: -f2)
SESSION_ID=$(generate_session_id "$client_ip" "$code")
sed -i "/^$code:/d" "$CODES_FILE" 2>/dev/null || true
log_used_code "$code" "$client_ip"
log_session "$SESSION_ID" "$client_ip" "$code" "$DURATION"
add_firewall_rule "$client_ip"
json_response '{"success": true, "message": "✓ Activado. Tienes acceso por '$DURATION' minutos.", "session_id": "'$SESSION_ID'", "expires_in": '$((DURATION * 60))'}'
exit 0
PORTAL_EOF
echo "✓ portal-api-v2.sh copiado"
```

---

## 📝 Paso 4: Copiar session-cleanup.sh

**Copia-pega COMPLETO en OpenWrt:**

```bash
cat > /usr/local/bin/session-cleanup.sh << 'CLEANUP_EOF'
#!/bin/sh
SESSIONS_FILE="/var/cache/jadslink/sessions.db"
SESSION_LOG="/var/log/jadslink/sessions.log"
EXPIRED_LOG="/var/log/jadslink/expired_sessions.log"

mkdir -p /var/cache/jadslink /var/log/jadslink

remove_firewall_rule() {
    local client_ip="$1"
    nft list table inet jadslink --handle 2>/dev/null | grep "ip saddr $client_ip" | while read -r line; do
        handle=$(echo "$line" | grep -o 'handle [0-9]*' | cut -d' ' -f2 | tail -1)
        [ -n "$handle" ] && nft delete rule inet jadslink forward handle "$handle" 2>/dev/null || true
    done
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
CLEANUP_EOF
echo "✓ session-cleanup.sh copiado"
```

---

## 📝 Paso 5: Copiar jadslink-firewall-v2.sh

**Copia-pega COMPLETO en OpenWrt:**

```bash
cat > /usr/local/bin/jadslink-firewall-v2.sh << 'FIREWALL_EOF'
#!/bin/sh
LAN_SUBNET="192.168.1.0/24"
ROUTER_IP="192.168.1.1"

nft list table inet jadslink > /dev/null 2>&1 || nft add table inet jadslink
nft list chain inet jadslink prerouting > /dev/null 2>&1 || nft add chain inet jadslink prerouting '{ type nat hook prerouting priority dstnat + 1 ; policy accept ; }'
nft list chain inet jadslink prerouting | grep -q "udp dport 53 accept" || nft add rule inet jadslink prerouting udp dport 53 accept
nft list chain inet jadslink postrouting > /dev/null 2>&1 || nft add chain inet jadslink postrouting '{ type nat hook postrouting priority srcnat + 1 ; policy accept ; }'
nft list chain inet jadslink postrouting | grep -q "masquerade" || nft add rule inet jadslink postrouting ip saddr "$LAN_SUBNET" ip daddr != "$LAN_SUBNET" counter masquerade
nft list chain inet jadslink forward > /dev/null 2>&1 || nft add chain inet jadslink forward '{ type filter hook forward priority filter + 1 ; policy accept ; }'
nft list chain inet jadslink forward | grep -q "established,related accept" || nft add rule inet jadslink forward ct state established,related counter accept
nft list chain inet jadslink forward | grep -q "ip daddr $ROUTER_IP counter accept" || nft add rule inet jadslink forward ip daddr "$ROUTER_IP" counter accept
nft list chain inet jadslink forward | grep -q "ip daddr $LAN_SUBNET counter accept" || nft add rule inet jadslink forward ip daddr "$LAN_SUBNET" counter accept
nft list chain inet jadslink forward | grep -q "BLOCK_UNAUTH" || nft add rule inet jadslink forward ip saddr "$LAN_SUBNET" ip daddr != "$LAN_SUBNET" counter drop comment "BLOCK_UNAUTH"
echo "✓ Firewall initialized"
FIREWALL_EOF
echo "✓ jadslink-firewall-v2.sh copiado"
```

---

## 📝 Paso 6: Copiar jadslink-session-cleanup.init

**Copia-pega COMPLETO en OpenWrt:**

```bash
cat > /etc/init.d/jadslink-session-cleanup << 'INIT_EOF'
#!/bin/sh /etc/rc.common
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
INIT_EOF
echo "✓ jadslink-session-cleanup.init copiado"
```

---

## ⚙️ Paso 7: Dar Permisos

**Copia-pega en OpenWrt:**

```bash
chmod 755 /www/cgi-bin/portal-api-v2.sh /usr/local/bin/session-cleanup.sh /usr/local/bin/jadslink-firewall-v2.sh /etc/init.d/jadslink-session-cleanup && echo "✓ Permisos configurados"
```

---

## 🚀 Paso 8: Inicializar Servicios

**Copia-pega en OpenWrt:**

```bash
/usr/local/bin/jadslink-firewall-v2.sh && echo "✓ Firewall inicializado"
```

**Luego copia-pega:**

```bash
/etc/init.d/jadslink-session-cleanup start && /etc/init.d/jadslink-session-cleanup enable && echo "✓ Session cleanup iniciado"
```

---

## 💾 Paso 9: Crear Códigos de Demostración

**Copia-pega en OpenWrt:**

```bash
cat > /var/cache/jadslink/demo_tickets.db << 'EOF'
ABC123XYZ:30
DEF456UVW:60
GHI789RST:1440
TEST001:30
TEST002:60
TEST003:1440
TICKET001:30
TICKET002:60
TICKET003:1440
EOF

chmod 644 /var/cache/jadslink/demo_tickets.db && echo "✓ Códigos creados"
```

---

## ✅ Paso 10: Verificar Instalación

**Copia-pega en OpenWrt:**

```bash
echo ""
echo "VERIFICACIÓN:"
echo ""
echo "1. Firewall:"
nft list table inet jadslink > /dev/null && echo "   ✓ OK" || echo "   ✗ ERROR"
echo ""
echo "2. Session cleanup:"
ps aux | grep -q "[s]ession-cleanup" && echo "   ✓ OK" || echo "   ✗ ERROR"
echo ""
echo "3. Portal CGI:"
[ -x /www/cgi-bin/portal-api-v2.sh ] && echo "   ✓ OK" || echo "   ✗ ERROR"
echo ""
echo "4. Códigos:"
[ -f /var/cache/jadslink/demo_tickets.db ] && echo "   ✓ OK ($(wc -l < /var/cache/jadslink/demo_tickets.db) códigos)" || echo "   ✗ ERROR"
echo ""
echo "✅ DEPLOYMENT COMPLETADO"
```

---

## 🧪 Testing Inmediato

**Desde tu cliente WiFi:**

1. **Conecta** a red: `JADSlink-Hotspot`
2. **Abre navegador**: `http://google.com`
3. Portal debe aparecer automáticamente
4. **Ingresa código**: `ABC123XYZ`
5. **Presiona**: Activar
6. Verás: "✓ Activado. Tienes acceso por 30 minutos."
7. **Navega a**: `http://facebook.com` — ✓ Funciona
8. **Prueba código no reutilizable**:
   - Desconecta WiFi
   - Reconecta
   - Intenta `ABC123XYZ` → ✗ Rechazado
   - Intenta `DEF456UVW` → ✓ Funciona

---

## 📋 Checklist

- [ ] Conectado a OpenWrt vía SSH
- [ ] Directorios creados
- [ ] portal-api-v2.sh copiado ✓
- [ ] session-cleanup.sh copiado ✓
- [ ] jadslink-firewall-v2.sh copiado ✓
- [ ] jadslink-session-cleanup.init copiado ✓
- [ ] Permisos dados
- [ ] Firewall inicializado ✓
- [ ] Session cleanup iniciado ✓
- [ ] Códigos creados ✓
- [ ] Verificación muestra ✓ en todo
- [ ] Cliente WiFi conectado
- [ ] Portal aparece automáticamente
- [ ] Código funciona en primer intento
- [ ] Código rechazado en segundo intento

---

## ✨ Resultado

```
✅ DEPLOYMENT COMPLETADO EXITOSAMENTE

Archivo de scripts: /www/cgi-bin/portal-api-v2.sh
Cleanup automático: /usr/local/bin/session-cleanup.sh
Firewall: /usr/local/bin/jadslink-firewall-v2.sh
Init service: /etc/init.d/jadslink-session-cleanup

Códigos disponibles: 9 (ABC123XYZ, DEF456UVW, etc.)

Status: 🟢 LISTO PARA TESTING
```

---

**¡Ahora conecta tu cliente WiFi y prueba!** 🚀
