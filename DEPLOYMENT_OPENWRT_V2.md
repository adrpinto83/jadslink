# JADSlink OpenWrt Deployment v2
## Implementación de Códigos One-Time y Session Management

**Fecha**: 2026-05-01
**Estado**: Listo para deployment
**Mejoras principales**:
- ✅ Códigos de una sola uso
- ✅ Expiración automática de sesiones
- ✅ Aislamiento de tráfico entre clientes
- ✅ Logging completo de sesiones

---

## 📋 Archivos a Desplegar

```
openwrt-scripts/
├── portal-api-v2.sh                 ← CGI script mejorado
├── session-cleanup.sh               ← Limpieza automática de sesiones
├── jadslink-session-cleanup.init    ← Init script para OpenWrt
└── jadslink-firewall-v2.sh         ← Configuración firewall mejorada
```

---

## 🚀 Pasos de Deployment

### PASO 1: Conectar a OpenWrt por SSH

```bash
# Desde tu máquina
ssh root@192.168.0.10
# Password: 123456 (o la que hayas configurado)
```

### PASO 2: Crear directorios necesarios

```bash
# En OpenWrt console:
mkdir -p /usr/local/bin
mkdir -p /var/cache/jadslink
mkdir -p /var/log/jadslink
mkdir -p /etc/init.d
```

### PASO 3: Copiar los scripts

**Opción A: Via SCP (Recomendado)**

```bash
# Desde tu máquina host:
scp openwrt-scripts/portal-api-v2.sh root@192.168.0.10:/www/cgi-bin/
scp openwrt-scripts/session-cleanup.sh root@192.168.0.10:/usr/local/bin/
scp openwrt-scripts/jadslink-session-cleanup.init root@192.168.0.10:/etc/init.d/
scp openwrt-scripts/jadslink-firewall-v2.sh root@192.168.0.10:/usr/local/bin/
```

**Opción B: Via copy-paste en consola**

1. Abrir `/www/cgi-bin/portal-api-v2.sh` en tu editor
2. Copiar COMPLETO
3. En OpenWrt console:
   ```bash
   cat > /www/cgi-bin/portal-api-v2.sh << 'EOF'
   [PEGA AQUÍ EL CONTENIDO]
   EOF
   ```
4. Repetir para los otros scripts

### PASO 4: Dar permisos de ejecución

```bash
# En OpenWrt:
chmod +x /www/cgi-bin/portal-api-v2.sh
chmod +x /usr/local/bin/session-cleanup.sh
chmod +x /etc/init.d/jadslink-session-cleanup
chmod +x /usr/local/bin/jadslink-firewall-v2.sh
```

### PASO 5: Actualizar configuración de uhttpd

```bash
# En OpenWrt:
# Editar /etc/config/uhttpd o vía UCI:
uci set uhttpd.main.cgi_prefix="/cgi-bin"
uci set uhttpd.main.cgi_program="/usr/bin/cgi"  # Si no está

uci commit uhttpd
/etc/init.d/uhttpd restart
```

### PASO 6: Actualizar dnsmasq.conf

```bash
# En OpenWrt:
# Verificar que tenga las redirecciones para captive portal:
cat /etc/dnsmasq.conf | grep "address="

# Si falta, agregar:
cat >> /etc/dnsmasq.conf << 'EOF'

# JADSlink Captive Portal DNS
address=/captive.apple.com/192.168.1.1
address=/connectivitycheck.android.com/192.168.1.1
address=/clients3.google.com/192.168.1.1
address=/connectivity-check.firefox.com/192.168.1.1
address=/www.msftncsi.com/192.168.1.1
address=/generate_204/192.168.1.1
address=/hotspot-detect.html/192.168.1.1
EOF

/etc/init.d/dnsmasq restart
```

### PASO 7: Inicializar firewall

```bash
# En OpenWrt:
/usr/local/bin/jadslink-firewall-v2.sh

# Verificar que se inicializó:
nft list table inet jadslink
```

### PASO 8: Crear archivo de códigos de demostración

```bash
# En OpenWrt:
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

# Permisos
chmod 644 /var/cache/jadslink/demo_tickets.db
```

### PASO 9: Habilitar servicio de limpieza de sesiones

```bash
# En OpenWrt:
/etc/init.d/jadslink-session-cleanup start
/etc/init.d/jadslink-session-cleanup enable

# Verificar:
/etc/init.d/jadslink-session-cleanup status
```

### PASO 10: Hacer firewall persistente

```bash
# En OpenWrt:
# Editar /etc/rc.local para que ejecute el firewall al boot:

cat >> /etc/rc.local << 'EOF'

# JADSlink Firewall Init
/usr/local/bin/jadslink-firewall-v2.sh &

EOF

# O usar init script
/etc/init.d/jadslink-firewall start
/etc/init.d/jadslink-firewall enable
```

---

## 🧪 Testing Post-Deployment

### Test 1: Verificar que portal-api-v2.sh está activo

```bash
# En OpenWrt:
ls -la /www/cgi-bin/portal-api-v2.sh
file /www/cgi-bin/portal-api-v2.sh  # Debe ser "shell script"
```

### Test 2: Simular POST request al CGI

```bash
# En OpenWrt:
# Crear código temporal en demo_tickets.db
echo "TESTCODE001:30" >> /var/cache/jadslink/demo_tickets.db

# Simular POST (opcional - solo si tienes curl):
# curl -X POST http://127.0.0.1/cgi-bin/portal-api-v2.sh \
#   -d "action=activate&code=TESTCODE001&client_ip=192.168.1.100"
```

### Test 3: Conectar cliente WiFi real

```
1. Desde tu laptop/phone:
   - Conecta a: JADSlink-Hotspot
   - Sin contraseña
   - Espera DHCP (5-10 segundos)

2. Abre navegador:
   - Ve a: http://google.com
   - Portal debe aparecer automáticamente

3. Ingresa código:
   - ABC123XYZ
   - Presiona Activar

4. Verifica:
   - ✓ Portal muestra: "✓ Activado. Tienes acceso por 30 minutos."
   - ✓ Puedes navegar a google.com
   - ✓ Puedes acceder a otros sitios (facebook.com, etc.)
```

### Test 4: Verificar código no reutilizable

```
1. Desde MISMO cliente:
   - Desconecta WiFi
   - Reconecta a JADSlink-Hotspot

2. Abre navegador:
   - Ve a: http://google.com
   - Portal debe aparecer

3. Intenta usar MISMO código:
   - ABC123XYZ
   - Error: "Código ya fue utilizado y expiró"
   - ✓ CORRECTO - código es one-time

4. Intenta con código DIFERENTE:
   - DEF456UVW
   - Debe funcionar
   - ✓ CORRECTO
```

### Test 5: Verificar aislamiento de tráfico

```
1. Cliente A (192.168.1.100):
   - Conecta y activa código ABC123XYZ
   - Puede acceder a internet

2. Cliente B (192.168.1.101):
   - INTENTA acceder sin código
   - NO puede llegar a internet
   - Solo ve portal

3. Cliente B luego activa:
   - Ingresa código DEF456UVW
   - Ahora SÍ puede acceder a internet

✓ Tráfico está aislado - cada cliente necesita su código
```

### Test 6: Verificar timeout de sesión

```
1. Activar código con duración 30 minutos:
   - ABC123XYZ → 30 minutos

2. Esperar a que expire la sesión (o modificar demo_tickets.db):
   - Cambiar a: ABC123XYZ:1 (1 minuto para test)

3. Despué de timeout:
   - Cliente pierde acceso a internet
   - Vuelve a ver portal
   - Puede activar NUEVO código
```

---

## 📊 Archivos Generados en Tiempo de Ejecución

### Cache y Sesiones

**`/var/cache/jadslink/demo_tickets.db`**
```
ABC123XYZ:30
DEF456UVW:60
...
```

**`/var/cache/jadslink/used_codes.db`**
```
ABC123XYZ:192.168.1.100:1714512345
```

**`/var/cache/jadslink/sessions.db`**
```
a1b2c3d4e5f6g7h8:192.168.1.100:ABC123XYZ:1714512345:30:active
```

### Logs

**`/var/log/jadslink/sessions.log`**
```
[2026-05-01 14:30:45] Session=a1b2c3d4e5f6g7h8 IP=192.168.1.100 Code=ABC123XYZ Duration=30
[2026-05-01 14:31:20] Session=x9y8z7w6v5u4t3s2 IP=192.168.1.101 Code=DEF456UVW Duration=60
```

**`/var/log/jadslink/used_codes.log`**
```
[2026-05-01 14:30:45] Code=ABC123XYZ UsedBy=192.168.1.100
```

**`/var/log/jadslink/expired_sessions.log`**
```
[2026-05-01 15:00:45] ExpiredSession=a1b2c3d4e5f6g7h8 IP=192.168.1.100 Code=ABC123XYZ Duration=30
```

**`/var/log/jadslink/cleanup.log`**
```
(logs de ejecución del script de limpieza)
```

---

## 🔧 Troubleshooting Post-Deployment

### Problema: "POST request returns 500 error"

```bash
# En OpenWrt, verificar permisos:
ls -la /www/cgi-bin/portal-api-v2.sh
# Debe ser: -rwxr-xr-x (755)

# Si no, arreglar:
chmod 755 /www/cgi-bin/portal-api-v2.sh

# Reiniciar uhttpd:
/etc/init.d/uhttpd restart
```

### Problema: "CGI script not found"

```bash
# Verificar que uhttpd tiene CGI habilitado:
cat /etc/config/uhttpd | grep -i cgi

# Si falta, agregar:
uci set uhttpd.main.cgi_prefix="/cgi-bin"
uci commit uhttpd
/etc/init.d/uhttpd restart
```

### Problema: "Códigos no se validan"

```bash
# Verificar que demo_tickets.db existe:
ls -la /var/cache/jadslink/demo_tickets.db

# Verificar contenido:
cat /var/cache/jadslink/demo_tickets.db

# Si está vacío, recrear:
cat > /var/cache/jadslink/demo_tickets.db << 'EOF'
ABC123XYZ:30
DEF456UVW:60
...
EOF

chmod 644 /var/cache/jadslink/demo_tickets.db
```

### Problema: "Session cleanup no funciona"

```bash
# Verificar que está corriendo:
ps aux | grep "session-cleanup"

# Verificar logs:
tail -20 /var/log/jadslink/cleanup.log

# Si no está corriendo, iniciar manualmente:
/etc/init.d/jadslink-session-cleanup start

# Y habilitarlo para auto-start:
/etc/init.d/jadslink-session-cleanup enable
```

### Problema: "Firewall rules no persisten después de reboot"

```bash
# Verificar que /etc/rc.local ejecuta el firewall:
cat /etc/rc.local | grep jadslink-firewall

# Si no aparece, agregar:
echo "/usr/local/bin/jadslink-firewall-v2.sh &" >> /etc/rc.local

# O usar init script:
/etc/init.d/jadslink-firewall enable
```

---

## 📋 Checklist de Deployment Completo

- [ ] SSH conectado a OpenWrt (192.168.0.10)
- [ ] Directorios creados (/usr/local/bin, /var/cache/jadslink, etc)
- [ ] Scripts copiados a sus ubicaciones
- [ ] Permisos de ejecución dados (755)
- [ ] uhttpd configurado con CGI
- [ ] dnsmasq con redirecciones de DNS
- [ ] demo_tickets.db creado con códigos
- [ ] Firewall inicializado (nft table creada)
- [ ] Session cleanup service activo
- [ ] Servicios persistentes tras reboot
- [ ] Test de cliente WiFi exitoso
- [ ] Códigos no reutilizables validados
- [ ] Timeout de sesión validado

---

## 🎯 Estado Final

Una vez completado este deployment:

✅ **Códigos one-time**: Cada código se puede usar UNA SOLA VEZ
✅ **Aislamiento**: Cada cliente necesita su propio código
✅ **Timeout automático**: Sesiones expiran automáticamente
✅ **Sin reuso**: Códigos usados se eliminan del sistema
✅ **Firewall strict**: Default-DENY para unauthenticados

**Sistema listo para Fase 2.3: Integración con Backend API**

---

## 📞 Próximos Pasos

### Fase 2.3: Integración Backend
- Reemplazar demo_tickets.db con API backend
- Generar códigos dinámicos en 192.168.0.201:8000
- Validar contra base de datos en tiempo real

### Fase 2.4: E2E Testing
- Probar con múltiples clientes simultáneamente
- Validar límites de conexiones concurrentes
- Stress testing con alta rotación de usuarios

**Documentación**: OPENWRT_API_INTEGRATION.md (siguiente fase)
