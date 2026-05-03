# 🚀 DEPLOYMENT SIN SCP — Para OpenWrt sin SFTP Server

**Problema**: `scp: Connection closed` - OpenWrt no tiene sftp-server

**Solución**: Usar SSH con heredoc para copiar archivos

---

## ⚡ OPCIÓN 1: Script Automático (RECOMENDADO)

### Paso 1: Asegurarse de tener los datos

```bash
# En tu máquina:
cd /home/adrpinto/jadslink

# Verificar que existe:
ls -la DEPLOY_VIA_SSH.sh
# -rw-r--r-- ... DEPLOY_VIA_SSH.sh
```

### Paso 2: Ejecutar script de deployment

```bash
# En tu máquina (NO en OpenWrt):
bash DEPLOY_VIA_SSH.sh

# El script hará automáticamente:
# - Conectar a OpenWrt
# - Crear directorios
# - Copiar todos los scripts (vía SSH heredoc)
# - Dar permisos
# - Inicializar servicios
# - Crear códigos
# - Verificar instalación
```

### Resultado esperado

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     JADSlink FASE 2.2 v2 — Deployment via SSH                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

[1/5] Creando directorios...
✓ Directorios creados

[2/5] Copiando scripts...
  Copiando portal-api-v2.sh... ✓
  Copiando session-cleanup.sh... ✓
  Copiando jadslink-firewall-v2.sh... ✓
  Copiando jadslink-session-cleanup.init... ✓

[3/5] Dando permisos de ejecución...
✓ Permisos configurados

[4/5] Inicializando servicios...
✓ Firewall inicializado
✓ Session cleanup service iniciado

[5/5] Creando códigos de demostración...
✓ Códigos de demostración creados

═══════════════════════════════════════════════════════════════

VERIFICACIÓN DEL DEPLOYMENT:

1. Firewall:
   ✓ Tabla nftables 'inet jadslink' EXISTS

2. Session cleanup service:
   ✓ Session cleanup está CORRIENDO

3. Portal CGI:
   ✓ portal-api-v2.sh EXISTS y es EXECUTABLE

4. Códigos de demostración:
   ✓ demo_tickets.db EXISTS con 9 códigos

═══════════════════════════════════════════════════════════════

✅ DEPLOYMENT COMPLETADO EXITOSAMENTE
```

---

## 🔧 OPCIÓN 2: Manual con SSH (Si DEPLOY_VIA_SSH.sh falla)

### Paso 1: Conectar a OpenWrt

```bash
ssh root@192.168.0.10
# Password: 123456
```

### Paso 2: Crear directorios

```bash
# En OpenWrt:
mkdir -p /www/cgi-bin
mkdir -p /usr/local/bin
mkdir -p /etc/init.d
mkdir -p /var/cache/jadslink
mkdir -p /var/log/jadslink
```

### Paso 3: Crear portal-api-v2.sh

```bash
# En OpenWrt, pega TODO esto (de una vez):
cat > /www/cgi-bin/portal-api-v2.sh << 'PORTAL_EOF'
#!/bin/sh
#
# JADSlink Portal API v2
# [... contenido completo del script ...]
#
PORTAL_EOF
```

**Contenido**: Ver archivo `/home/adrpinto/jadslink/openwrt-scripts/portal-api-v2.sh`

### Paso 4: Copiar otros scripts

Repetir Paso 3 para:
- `/usr/local/bin/session-cleanup.sh` (contenido: `openwrt-scripts/session-cleanup.sh`)
- `/usr/local/bin/jadslink-firewall-v2.sh` (contenido: `openwrt-scripts/jadslink-firewall-v2.sh`)
- `/etc/init.d/jadslink-session-cleanup` (contenido: `openwrt-scripts/jadslink-session-cleanup.init`)

### Paso 5: Dar permisos

```bash
# En OpenWrt:
chmod 755 /www/cgi-bin/portal-api-v2.sh
chmod 755 /usr/local/bin/session-cleanup.sh
chmod 755 /usr/local/bin/jadslink-firewall-v2.sh
chmod 755 /etc/init.d/jadslink-session-cleanup
```

### Paso 6: Inicializar servicios

```bash
# En OpenWrt:
/usr/local/bin/jadslink-firewall-v2.sh
/etc/init.d/jadslink-session-cleanup start
/etc/init.d/jadslink-session-cleanup enable
```

### Paso 7: Crear códigos

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

chmod 644 /var/cache/jadslink/demo_tickets.db
```

### Paso 8: Verificar

```bash
# En OpenWrt:
nft list table inet jadslink | head -3
ps aux | grep session-cleanup
cat /var/cache/jadslink/demo_tickets.db
```

---

## 📝 Alternativa 3: Copy-Paste Interactivo (Más Lento)

Si DEPLOY_VIA_SSH.sh no funciona, usa DEPLOY_OPENWRT_SCRIPT.sh directamente:

```bash
# 1. Conectar a OpenWrt
ssh root@192.168.0.10

# 2. Crear archivo de script
cat > /tmp/deploy.sh << 'EOF'
# COPIAR COMPLETO desde:
# /home/adrpinto/jadslink/DEPLOY_OPENWRT_SCRIPT.sh
EOF

# 3. Ejecutar
bash /tmp/deploy.sh
```

---

## ✅ Testing Post-Deployment

### Verificación rápida en OpenWrt

```bash
# Firewall activo
nft list table inet jadslink | wc -l
# Debe mostrar: > 0

# Session cleanup corriendo
ps aux | grep session-cleanup | grep -v grep
# Debe mostrar: /bin/sh -c while true...

# Códigos creados
cat /var/cache/jadslink/demo_tickets.db
# Debe mostrar: ABC123XYZ:30 ...

# Portal CGI disponible
test -x /www/cgi-bin/portal-api-v2.sh && echo "✓ CGI OK" || echo "✗ CGI ERROR"
```

### Test desde cliente WiFi

```
1. Desde tu laptop/phone:
   - Conecta a: JADSlink-Hotspot
   - Abre: http://google.com

2. Portal debe aparecer automáticamente

3. Ingresa código: ABC123XYZ

4. Deberías ver: "✓ Activado. Tienes acceso por 30 minutos."

5. Intenta navegar: http://facebook.com

Si todo funciona: ✅ DEPLOYMENT OK
```

---

## 🔧 Troubleshooting

### Error: "Connection refused" en SSH

```bash
# Verificar que SSH está habilitado en OpenWrt
ssh root@192.168.0.10 'ps aux | grep dropbear'

# Si no aparece dropbear, necesitas habilitarlo:
# Ver: OPENWRT_MANUAL_SETUP_CONSOLE.md
```

### Error: "Password authentication failed"

```bash
# Verificar password correcto:
ssh root@192.168.0.10
# Intenta: root (sin contraseña) o 123456

# Si no funciona, conectar vía Proxmox Console y cambiar:
# passwd root
# Ingresa nueva contraseña
```

### Script DEPLOY_VIA_SSH.sh falla

Opciones:
1. Instalar sshpass: `apt-get install sshpass` (en tu máquina)
2. Usar Opción 2 (Manual con SSH)
3. Usar OPENWRT_MANUAL_SETUP_CONSOLE.md (línea por línea)

### Archivos no se copiaron

Verificar en OpenWrt:

```bash
# Portal CGI
ls -la /www/cgi-bin/portal-api-v2.sh

# Cleanup script
ls -la /usr/local/bin/session-cleanup.sh

# Firewall
ls -la /usr/local/bin/jadslink-firewall-v2.sh

# Init service
ls -la /etc/init.d/jadslink-session-cleanup

# Códigos
ls -la /var/cache/jadslink/demo_tickets.db
```

Si falta algo, usar Opción 2 (Manual con SSH)

---

## 📋 Checklist

- [ ] Puedo conectar a OpenWrt vía SSH
- [ ] Password SSH funciona (123456)
- [ ] DEPLOY_VIA_SSH.sh existe en mi máquina
- [ ] He ejecutado: `bash DEPLOY_VIA_SSH.sh`
- [ ] Veo "✅ DEPLOYMENT COMPLETADO EXITOSAMENTE"
- [ ] Todos los archivos están en OpenWrt
- [ ] Cliente WiFi ve red: JADSlink-Hotspot
- [ ] Portal aparece automáticamente
- [ ] Código ABC123XYZ funciona en primer intento
- [ ] Mismo código rechazado en segundo intento

---

## ✨ Resultado Final

```
✅ DEPLOYMENT COMPLETADO SIN SCP

Métodos disponibles:
1. DEPLOY_VIA_SSH.sh      (Recomendado - automático)
2. Manual con SSH         (Si #1 falla)
3. OPENWRT_MANUAL_SETUP   (Último recurso)

Estado: 🟢 SISTEMA OPERATIVO
```

---

**¿Cuál método prefieres?**
1. **DEPLOY_VIA_SSH.sh** (Automático - 2 min)
2. **Manual con SSH** (Copy-paste)
3. **OPENWRT_MANUAL_SETUP_CONSOLE.md** (Línea por línea)

Ejecuta lo siguiente en tu máquina:

```bash
bash /home/adrpinto/jadslink/DEPLOY_VIA_SSH.sh
```

Si pide password SSH en varios puntos, ingresa: `123456`
