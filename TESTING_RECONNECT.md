# ✅ Testing Portal Captive — Verificar Reconexión

**Fecha**: 2026-05-01
**Fase**: 2.2
**Objetivo**: Verificar que el portal aparece automáticamente en reconexión

---

## 📋 Configuración Actual

```
OpenWrt VM: 192.168.0.10 (ssh root@192.168.0.10, password: 123456)
Portal IP: 192.168.1.1:80
WiFi SSID: JADSlink-Hotspot (abierta, sin contraseña)
```

### Servicios Activos
- ✅ uhttpd (puerto 80) — sirviendo portal HTML
- ✅ dnsmasq (puerto 53) — redirigiendo dominios de detección
- ✅ nftables — redirect HTTP a portal

### Reglas Firewall
```
tcp dport 80 (ANY destination excepto 192.168.1.1) → redirect a 80
udp dport 53 → aceptado
IP 192.168.1.0/24 → acceso a portal
```

### DNS Redirect
Los siguientes dominios resuelven a `192.168.1.1`:
- `captive.apple.com` (iOS/macOS)
- `connectivitycheck.android.com` (Android)
- `clients3.google.com` (Chrome)
- `connectivity-check.firefox.com` (Firefox)
- `www.msftncsi.com` (Windows)

---

## 🧪 Test 1: Primera Conexión (Debe mostrar portal automáticamente)

### Pasos

1. **Desconecta** de cualquier red
2. **Busca WiFi** y conecta a: `JADSlink-Hotspot`
   - Sin contraseña
   - Espera 3-5 segundos para DHCP
3. **Abre navegador** y ve a: `http://google.com`
   - NO escribas IP (192.168.1.1)
   - Déjalo que redireccionara automáticamente

### Resultado Esperado ✅

```
┌─────────────────────────────────┐
│     🌐 JADSlink                 │
│                                 │
│   Acceso a Internet Satelital   │
│                                 │
│   Código de Acceso              │
│   [_______________________]     │
│                                 │
│       [  Activar  ]             │
│                                 │
│   ¿Cómo obtener un código?      │
│   Contacta al operador          │
└─────────────────────────────────┘
```

**Si ves esto**: ✅ **Primera conexión funciona**

---

## 🔄 Test 2: Reconexión (Debe mostrar portal nuevamente)

### Pasos

1. Desde la misma pantalla del portal
2. **Desconecta WiFi** (settings → "Olvidar red")
3. **Reconecta a** `JADSlink-Hotspot`
   - Espera 3-5 segundos para DHCP
4. **Abre navegador** nuevamente: `http://google.com`

### Resultado Esperado ✅

El portal debe aparecer **automáticamente** nuevamente en ~5-10 segundos.

**Si aparece**: ✅ **Reconexión funciona** (FASE 2.2 COMPLETA)
**Si NO aparece**: ❌ **Necesita debug** (ver sección Troubleshooting)

---

## 🎯 Test 3: Validación de Códigos

### Códigos de Prueba Disponibles

```
ABC123XYZ    → 30 minutos
DEF456UVW    → 60 minutos
GHI789RST    → 1440 minutos (1 día)
TEST001      → 30 minutos
TICKET001    → 30 minutos
```

### Pasos

1. En el portal, ingresa código: `ABC123XYZ`
2. Presiona **"Activar"**
3. Debes ver: `✓ Activado. Tienes acceso por 30 minutos.`

### Resultado Esperado ✅

```json
{
  "success": true,
  "message": "✓ Activado. Tienes acceso por 30 minutos."
}
```

**Si ves esto**: ✅ **Validación funciona**

---

## 🌐 Test 4: Navegación Post-Autenticación

### Pasos

1. Después de activar código (Test 3)
2. Intenta navegar a: `http://example.com` o `http://google.com`

### Resultado Esperado ✅

Debes poder acceder a sitios externos (no bloqueado por firewall).

**Si funciona**: ✅ **Acceso a internet concedido**

---

## 🔴 Troubleshooting

### Problema: Portal NO aparece automáticamente en reconexión

#### Paso 1: Verificar que dnsmasq responde

```bash
# Desde el cliente:
nslookup captive.apple.com 192.168.1.1
# Debe responder: 192.168.1.1
```

Si no responde → **dnsmasq parado o mal configurado**

```bash
# Desde OpenWrt (ssh):
/etc/init.d/dnsmasq status
/etc/init.d/dnsmasq restart
```

#### Paso 2: Verificar que firewall redirige

```bash
# Desde OpenWrt:
nft list table inet jadslink
# Debe mostrar: tcp dport 80 ... redirect to :80
```

Si no hay reglas → **Cargar manualmente**:

```bash
/etc/init.d/jadslink-firewall start
```

#### Paso 3: Verificar que uhttpd escucha

```bash
# Desde OpenWrt:
netstat -tlnp 2>/dev/null | grep 80
# Debe mostrar: uhttpd LISTEN 0.0.0.0:80
```

Si no aparece → **Restart uhttpd**:

```bash
/etc/init.d/uhttpd restart
```

#### Paso 4: Probar portal directamente

```bash
# Desde cliente (conectado a WiFi):
wget -q -O - http://192.168.1.1 | head -5
# Debe mostrar HTML del portal
```

---

### Problema: Código NO se valida ("Sin conexión al servidor")

#### Causas posibles

1. **CGI script no existe o no tiene permisos**
   ```bash
   ls -la /www/cgi-bin/portal-api.sh
   # Debe estar executable (-rwxr-xr-x)
   ```

2. **Cache de códigos vacío o corrupto**
   ```bash
   cat /var/cache/jadslink/demo_tickets.db
   # Debe contener líneas como: ABC123XYZ:30
   ```

3. **uhttpd no tiene CGI habilitado**
   ```bash
   cat /etc/config/uhttpd | grep cgi_prefix
   # Debe mostrar: option cgi_prefix '/cgi-bin'
   ```

#### Solución

```bash
# Recrear cache
mkdir -p /var/cache/jadslink
cat > /var/cache/jadslink/demo_tickets.db << 'EOF'
ABC123XYZ:30
DEF456UVW:60
GHI789RST:1440
TEST001:30
TEST002:60
TEST003:1440
DEMO001:1440
DEMO002:1440
DEMO003:1440
TICKET001:30
TICKET002:60
TICKET003:1440
EOF

# Permisos
chmod 644 /var/cache/jadslink/demo_tickets.db

# Restart uhttpd
/etc/init.d/uhttpd restart
```

---

### Problema: Aparece portal pero se ve HTML quebrado

#### Causas

1. **Portal HTML corrupto o vacío**
   ```bash
   ls -lh /www/index.html
   # Debe ser > 7KB

   head -20 /www/index.html
   # Debe mostrar HTML válido
   ```

#### Solución

Recrear portal (ver documentación completa en `PORTAL_IMPLEMENTATION_COMPLETE.md`)

---

## ✅ Checklist de Completitud

- [ ] Test 1: Primera conexión muestra portal automáticamente
- [ ] Test 2: Reconexión muestra portal automáticamente
- [ ] Test 3: Códigos validan correctamente
- [ ] Test 4: Navegación post-autenticación funciona
- [ ] Firewall rules están persistentes (persisten tras reboot)
- [ ] dnsmasq redirige dominios de detección
- [ ] uhttpd escucha en puerto 80
- [ ] Portal HTML accesible en http://192.168.1.1

---

## 📊 Comandos de Debug Rápido

```bash
# En OpenWrt (ssh root@192.168.0.10)

# Verificar todo está corriendo
/etc/init.d/uhttpd status && /etc/init.d/dnsmasq status

# Ver logs de dnsmasq
tail -20 /var/log/dnsmasq.log

# Ver logs de agent
tail -20 /var/log/jadslink/agent.log

# Firewall
nft list table inet jadslink

# Test DNS
nslookup google.com 127.0.0.1 | head -5

# Test portal
wget -q -O - http://127.0.0.1 | head -3
```

---

## 🎯 Próximos Pasos (Si todo funciona)

Una vez que Tests 1-4 pasen:

### Fase 2.3: Integración Backend
- Generar tickets reales en backend (192.168.0.201:8000)
- Reemplazar cache local con API backend
- Ver: `OPENWRT_API_INTEGRATION.md`

### Fase 2.4: E2E Testing Completo
- Test con múltiples clientes simultáneamente
- Test de expiración de códigos
- Test de reconexión tras logout
- Ver: `OPENWRT_E2E_TESTING.md`

---

**¡A probar!** 🚀
