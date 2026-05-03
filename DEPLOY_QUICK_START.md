# 🚀 DEPLOYMENT RÁPIDO — 5 Pasos en OpenWrt

**Tiempo estimado**: 5 minutos
**Requisito**: Acceso SSH a OpenWrt (192.168.0.10)
**Password**: 123456

---

## ⚡ FORMA AUTOMÁTICA (Recomendado)

### Paso 1: Conectar a OpenWrt por SSH

```bash
# Desde tu máquina:
ssh root@192.168.0.10
# Password: 123456

# Si acepta, veras:
# root@OpenWrt:~#
```

### Paso 2: Descargar script de deployment

Opción A: Si tienes git:
```bash
# En OpenWrt:
cd /tmp
git clone https://github.com/adrpinto83/jadslink.git
cd jadslink
```

Opción B: Si no tienes git, copia-pega este script:

**IMPORTANTE**: Copia TODO el contenido de `/home/adrpinto/jadslink/DEPLOY_OPENWRT_SCRIPT.sh`

```bash
# En OpenWrt, ejecuta:
cat > /tmp/deploy.sh << 'EOF'
[PEGA TODO EL CONTENIDO DE DEPLOY_OPENWRT_SCRIPT.sh AQUÍ]
EOF
```

### Paso 3: Ejecutar script de deployment

```bash
# En OpenWrt:
bash /tmp/deploy.sh

# O si lo clonaste:
bash DEPLOY_OPENWRT_SCRIPT.sh
```

### Paso 4: Esperar a que termine

Verás output como:
```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     JADSlink FASE 2.2 v2 — Deployment Automático            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

[1/5] Creando directorios...
✓ Directorios creados

[2/5] Copiando scripts...
✓ portal-api-v2.sh copiado
...
```

### Paso 5: Verificar que funcionó

```bash
# En OpenWrt, verás al final:
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

**¡Listo!** El sistema está configurado.

---

## 🧪 TESTING INMEDIATO

### Test 1: Verificar servicios están corriendo

```bash
# En OpenWrt:
ps aux | grep session-cleanup
# Debe mostrar: /bin/sh -c while true; do /usr/local/bin/session-cleanup.sh ...

nft list table inet jadslink | head -5
# Debe mostrar: table inet jadslink { ...

cat /var/cache/jadslink/demo_tickets.db
# Debe mostrar: ABC123XYZ:30 ...
```

### Test 2: Conectar cliente WiFi

**Desde tu laptop/phone**:

1. **Desconecta** de cualquier WiFi
2. **Busca redes** disponibles
3. **Conecta a**: `JADSlink-Hotspot` (sin contraseña)
4. **Espera** 5-10 segundos (DHCP)
5. **Abre navegador**: `http://google.com`

**Resultado esperado**:
- ✅ Portal aparece automáticamente
- ✅ Ves campo "Código de Acceso"

### Test 3: Activar código

1. **En el portal**, ingresa: `ABC123XYZ`
2. **Presiona**: "Activar"
3. **Espera** 1-2 segundos

**Resultado esperado**:
- ✅ Portal muestra: "✓ Activado. Tienes acceso por 30 minutos."

### Test 4: Navegar

1. **Presiona**: "Continuar a Internet"
2. **Intenta**: `http://google.com`, `http://facebook.com`

**Resultado esperado**:
- ✅ Puedes acceder a internet

### Test 5: Código no reutilizable

1. **Desconecta** WiFi
2. **Reconecta** a `JADSlink-Hotspot`
3. **Abre**: `http://google.com`
4. **Portal reaparece**
5. **Intenta** `ABC123XYZ` nuevamente

**Resultado esperado**:
- ✗ Código rechazado: "Código ya fue utilizado y expiró"
- ✅ Usa código DIFERENTE: `DEF456UVW` → ✓ Funciona

---

## 🔧 Troubleshooting

### Problema: "SSH no conecta"

```bash
# Desde tu máquina:
ssh -v root@192.168.0.10

# Si dice "Connection refused":
# - OpenWrt no tiene SSH habilitado
# - Ver: OPENWRT_MANUAL_SETUP_CONSOLE.md

# Solución: Habilitar SSH en OpenWrt
uci set dropbear.@dropbear[0].enable=1
uci commit dropbear
/etc/init.d/dropbear start
```

### Problema: "El portal no aparece"

```bash
# En OpenWrt:
# 1. Verificar DNS
nslookup captive.apple.com 192.168.1.1
# Debe responder: 192.168.1.1

# 2. Verificar firewall
nft list chain inet jadslink forward
# Debe tener regla DROP

# 3. Verificar uhttpd
netstat -tulnp | grep :80
# Debe mostrar: uhttpd LISTEN 0.0.0.0:80

# Si falta uhttpd, reiniciar:
/etc/init.d/uhttpd restart
```

### Problema: "Código no se valida"

```bash
# En OpenWrt:
# 1. Verificar archivo de códigos
cat /var/cache/jadslink/demo_tickets.db
# Debe mostrar: ABC123XYZ:30 ...

# 2. Si está vacío, recrear:
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

# 3. Permisos:
chmod 644 /var/cache/jadslink/demo_tickets.db

# 4. Reiniciar uhttpd:
/etc/init.d/uhttpd restart
```

### Problema: "Session cleanup no está corriendo"

```bash
# En OpenWrt:
# 1. Verificar status:
/etc/init.d/jadslink-session-cleanup status

# 2. Si no está corriendo:
/etc/init.d/jadslink-session-cleanup start

# 3. Para auto-start en boot:
/etc/init.d/jadslink-session-cleanup enable

# 4. Verificar que está corriendo:
ps aux | grep session-cleanup
```

### Problema: "Timeout no funciona (sesión no expira)"

```bash
# En OpenWrt:
# 1. Verificar logs de cleanup:
tail -20 /var/log/jadslink/cleanup.log

# 2. Verificar sesiones activas:
cat /var/cache/jadslink/sessions.db

# 3. Si está vacío, activar un código:
# - Desde cliente: ingresar código
# - Esto debe crear entrada en sessions.db

# 4. Esperar 60 segundos
# 5. Verificar si expiró:
cat /var/log/jadslink/expired_sessions.log
```

---

## 📋 Checklist Post-Deployment

Antes de considerar que funcionó:

- [ ] SSH conectado a OpenWrt (192.168.0.10)
- [ ] Script ejecutado sin errores
- [ ] Verificación al final mostró ✓ en todo
- [ ] Cliente WiFi ve la red: JADSlink-Hotspot
- [ ] Cliente obtiene IP en rango 192.168.1.x
- [ ] Portal HTML aparece automáticamente
- [ ] Código ABC123XYZ se acepta en primer uso
- [ ] Cliente obtiene acceso a internet
- [ ] Mismo código rechazado en segundo intento
- [ ] Código diferente (DEF456UVW) funciona
- [ ] Logs se generan en /var/log/jadslink/

---

## 📊 Archivos Creados en OpenWrt

```
/www/cgi-bin/
└── portal-api-v2.sh          (CGI script)

/usr/local/bin/
├── session-cleanup.sh         (Cleanup automático)
└── jadslink-firewall-v2.sh    (Firewall init)

/etc/init.d/
└── jadslink-session-cleanup   (Init service)

/var/cache/jadslink/
├── demo_tickets.db            (Códigos disponibles)
├── used_codes.db              (Códigos usados - se crea automático)
└── sessions.db                (Sesiones activas - se crea automático)

/var/log/jadslink/
├── sessions.log               (Log de activaciones)
├── used_codes.log             (Log de códigos usados)
├── expired_sessions.log       (Log de expiración)
└── cleanup.log                (Log de limpieza)
```

---

## 🎯 Próximos Pasos (Si Todo Funciona)

1. **Fase 2.3**: Integración con Backend API
   - Reemplazar demo_tickets.db con API backend
   - Códigos dinámicos en 192.168.0.201:8000

2. **Fase 2.4**: E2E Testing
   - Testing con múltiples clientes
   - Testing de carga

---

## 📞 Si Algo Falla

**Consulta estos documentos** (en orden):

1. `README_FASE_2_2_V2.md` - Quick reference
2. `DEPLOYMENT_OPENWRT_V2.md` - Troubleshooting detallado
3. `OPENWRT_MANUAL_SETUP_CONSOLE.md` - Setup manual línea por línea

---

## ✅ Estado Final

```
✅ DEPLOYMENT COMPLETADO EXITOSAMENTE

Requisitos implementados:
✓ Bloquea a todos
✓ Muestra portal
✓ Acceso con código
✓ Código no reutilizable
✓ Sin compartir internet
✓ Expiración automática

Status: 🟢 LISTO PARA TESTING EN CLIENTE
```

---

**Hora**: 5 minutos
**Dificultad**: Principiante (copy-paste)
**Riesgo**: Muy bajo (no afecta servicios existentes)

**¡A desplegar!** 🚀
