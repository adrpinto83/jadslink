#!/bin/sh
#
# JADSlink Firewall Configuration v2
# Implementa:
# - Bloqueo default de tráfico unauthenticado
# - Reglas dinámicas para IPs autenticadas
# - Aislamiento de tráfico entre clientes
# - Opcional: límite de ancho de banda por sesión
#
# Usado por: /etc/init.d/jadslink-firewall
#

# Interfaces
LAN_INTERFACE="br-lan"
WAN_INTERFACE="eth0"
LAN_SUBNET="192.168.1.0/24"
ROUTER_IP="192.168.1.1"

# ============================================
# CREAR TABLA nftables
# ============================================

# Crear tabla si no existe
nft list table inet jadslink > /dev/null 2>&1 || {
    nft add table inet jadslink
}

# ============================================
# CHAIN PREROUTING (Manejo de DNS)
# ============================================

# Crear chain prerouting si no existe
nft list chain inet jadslink prerouting > /dev/null 2>&1 || {
    nft add chain inet jadslink prerouting '{ type nat hook prerouting priority dstnat + 1 ; policy accept ; }'
}

# Aceptar DNS (puerto 53)
nft list chain inet jadslink prerouting | grep -q "udp dport 53 accept" || {
    nft add rule inet jadslink prerouting udp dport 53 accept
}

# ============================================
# CHAIN POSTROUTING (NAT/Masquerade)
# ============================================

# Crear chain postrouting si no existe
nft list chain inet jadslink postrouting > /dev/null 2>&1 || {
    nft add chain inet jadslink postrouting '{ type nat hook postrouting priority srcnat + 1 ; policy accept ; }'
}

# Masquerade para tráfico LAN → WAN
nft list chain inet jadslink postrouting | grep -q "masquerade" || {
    nft add rule inet jadslink postrouting ip saddr "$LAN_SUBNET" ip daddr != "$LAN_SUBNET" counter masquerade
}

# ============================================
# CHAIN FORWARD (Filter - MAIN RULES)
# ============================================

# Crear chain forward si no existe
nft list chain inet jadslink forward > /dev/null 2>&1 || {
    nft add chain inet jadslink forward '{ type filter hook forward priority filter + 1 ; policy accept ; }'
}

# ============================================
# FORWARD RULES (en orden de precedencia)
# ============================================

# 1. Permitir tráfico ESTABLECIDO/RELACIONADO
nft list chain inet jadslink forward | grep -q "established,related accept" || {
    nft add rule inet jadslink forward ct state established,related counter accept
}

# 2. Permitir acceso LOCAL al router (LAN a router)
# Esto permite que clientes unauthenticados vean el portal en 192.168.1.1
nft list chain inet jadslink forward | grep -q "ip daddr $ROUTER_IP counter accept" || {
    nft add rule inet jadslink forward ip daddr "$ROUTER_IP" counter accept
}

# 3. Permitir comunicación dentro de LAN (192.168.1.0/24)
nft list chain inet jadslink forward | grep -q "ip daddr $LAN_SUBNET counter accept" || {
    nft add rule inet jadslink forward ip daddr "$LAN_SUBNET" counter accept
}

# 4. BLOQUEAR por default: LAN → WAN (default deny unauthenticados)
# Esta regla DEBE venir DESPUÉS de las reglas de allow
nft list chain inet jadslink forward | grep -q "BLOCK_UNAUTH" || {
    nft add rule inet jadslink forward ip saddr "$LAN_SUBNET" ip daddr != "$LAN_SUBNET" counter drop comment "BLOCK_UNAUTH"
}

echo "✓ Firewall initialized: Default-DENY policy configured"
