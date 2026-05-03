# 📁 Estructura de Archivos — FASE 2.2 v2

## Ubicación de Archivos en Repositorio Local

```
/home/adrpinto/jadslink/
│
├── openwrt-scripts/
│   ├── portal-api-v2.sh                 ← CGI mejorado (one-time codes)
│   ├── session-cleanup.sh               ← Limpieza automática
│   ├── jadslink-session-cleanup.init    ← Init service OpenWrt
│   └── jadslink-firewall-v2.sh          ← Firewall v2 (nftables)
│
├── Documentación Fase 2.2 v2:
│   ├── DEPLOYMENT_OPENWRT_V2.md                    ← EMPEZAR AQUÍ
│   ├── FASE_2_2_FINAL_REQUIREMENTS_VALIDATION.md   ← Testing
│   ├── FASE_2_2_V2_IMPLEMENTATION_SUMMARY.md       ← Detalles técnicos
│   ├── COMPARISON_V1_VS_V2.md                       ← Antes vs Después
│   ├── README_FASE_2_2_V2.md                        ← Quick reference
│   └── ESTRUCTURA_ARCHIVOS_FASE_2_2_V2.md          ← Este archivo
│
└── [Documentación anterior - existente]
    ├── OPENWRT_MANUAL_SETUP_CONSOLE.md
    ├── OPENWRT_CONFIG.md
    ├── FASE_2_2_FINAL_TESTING.md
    ├── TESTING_RECONNECT.md
    └── ... otros archivos
```

---

## Ubicación de Archivos en OpenWrt (Después de Deploy)

```
OpenWrt Router (192.168.0.10)
│
├── /www/cgi-bin/
│   └── portal-api-v2.sh                 ← CGI script mejorado
│                                          Recibe POST de portal
│                                          Valida códigos
│                                          Crea sesiones
│                                          Modifica firewall
│
├── /usr/local/bin/
│   ├── session-cleanup.sh               ← Limpieza automática
│   │                                     Ejecutado cada 60s
│   │                                     Expira sesiones
│   │                                     Remueve reglas firewall
│   │
│   └── jadslink-firewall-v2.sh          ← Inicialización firewall
│                                          Ejecutado en boot
│                                          Crea tabla nftables
│                                          Define chains y reglas
│
├── /etc/init.d/
│   └── jadslink-session-cleanup         ← Init service
│                                          Inicia cleanup loop
│                                          Auto-respawn
│                                          Compatible OpenWrt
│
├── /var/cache/jadslink/
│   ├── demo_tickets.db                  ← Códigos disponibles
│   │                                     Formato: CODE:DURATION_MIN
│   │                                     Se vacía al usar códigos
│   │
│   ├── used_codes.db                    ← Códigos consumidos
│   │                                     Formato: CODE:IP:TIMESTAMP
│   │                                     Auditoría de uso
│   │
│   └── sessions.db                      ← Sesiones activas
│                                          Formato: SESSION_ID:IP:CODE:TIMESTAMP:DURATION:STATUS
│                                          Tracking de sesiones
│
├── /var/log/jadslink/
│   ├── sessions.log                     ← Log de activaciones
│   │                                     [TIMESTAMP] Session=ID IP=... Code=... Duration=...
│   │
│   ├── used_codes.log                   ← Log de códigos usados
│   │                                     [TIMESTAMP] Code=... UsedBy=...
│   │
│   ├── expired_sessions.log             ← Log de expiración
│   │                                     [TIMESTAMP] ExpiredSession=... IP=...
│   │
│   └── cleanup.log                      ← Log de limpieza
│                                          Ejecución periódica
│
├── /etc/dnsmasq.conf                    ← Configuración DNS
│   (agregado):
│   address=/captive.apple.com/192.168.1.1
│   address=/connectivitycheck.android.com/192.168.1.1
│   ... (redirige auto-detection domains)
│
├── /etc/config/uhttpd                   ← Configuración HTTP server
│   (requiere):
│   option cgi_prefix '/cgi-bin'
│   (para ejecutar CGI scripts)
│
├── /etc/config/network                  ← Network config (ya existe)
│   (debe tener):
│   config interface 'lan'
│   option proto 'static'
│   option ipaddr '192.168.1.1'
│   option netmask '255.255.255.0'
│
├── /www/
│   ├── index.html                       ← Portal HTML (ya existe)
│   └── cgi-bin/
│       └── portal-api-v2.sh             ← CGI script (nuevo)
│
└── /etc/rc.local                        ← Script de boot (modificar)
    (agregar):
    /usr/local/bin/jadslink-firewall-v2.sh &
```

---

## Comparación: Archivos v1 vs v2

### ELIMINADOS (v1)
```
❌ portal-api.sh (versión antigua - reemplazada)
❌ authenticated_ips.txt (reemplazado por sessions.db)
```

### NUEVOS (v2)
```
✅ portal-api-v2.sh              ← CGI mejorado
✅ session-cleanup.sh            ← Script de limpieza (NUEVO)
✅ jadslink-session-cleanup.init ← Init service (NUEVO)
✅ jadslink-firewall-v2.sh       ← Firewall mejorado
✅ used_codes.db                 ← Auditoría de códigos
✅ sessions.db                   ← Tracking de sesiones
✅ expired_sessions.log          ← Log de expiración
✅ cleanup.log                   ← Log de limpieza
```

### MODIFICADOS/MEJORADOS
```
~ demo_tickets.db          ← Ahora se vacía al usar códigos
~ sessions.log             ← Formato mejorado
~ dnsmasq.conf             ← Redirecciones DNS (debe verificarse)
```

---

## Tamaño de Archivos

### Scripts (OpenWrt)
```
portal-api-v2.sh          ~2.5 KB    (CGI, con new features)
session-cleanup.sh        ~2 KB      (Cleanup automático)
jadslink-firewall-v2.sh   ~2 KB      (Firewall init)
jadslink-session-cleanup  ~1 KB      (Init script)
────────────────────────────────────
Total scripts:            ~7.5 KB    (negligible)
```

### Datos (Runtime)
```
demo_tickets.db           ~100 bytes  (10 códigos)
used_codes.db             ~50 B/uso   (crece con uso)
sessions.db               ~100 B/sesión (crece y se limpia)
sessions.log              ~100 B/activación
used_codes.log            ~50 B/código
expired_sessions.log      ~100 B/expiración
cleanup.log               ~100 B/ejecución
────────────────────────────────────
Total datos (per user):   ~500-1000 bytes
```

---

## Permisos de Archivos

### Scripts (deben ser ejecutables)
```bash
/www/cgi-bin/portal-api-v2.sh           755 (rwxr-xr-x)
/usr/local/bin/session-cleanup.sh       755 (rwxr-xr-x)
/usr/local/bin/jadslink-firewall-v2.sh  755 (rwxr-xr-x)
/etc/init.d/jadslink-session-cleanup    755 (rwxr-xr-x)
```

### Datos (lectura/escritura)
```bash
/var/cache/jadslink/demo_tickets.db     644 (rw-r--r--)
/var/cache/jadslink/used_codes.db       644 (rw-r--r--)
/var/cache/jadslink/sessions.db         644 (rw-r--r--)

/var/log/jadslink/sessions.log          644 (rw-r--r--)
/var/log/jadslink/used_codes.log        644 (rw-r--r--)
/var/log/jadslink/expired_sessions.log  644 (rw-r--r--)
/var/log/jadslink/cleanup.log           644 (rw-r--r--)
```

### Directorios
```bash
/var/cache/jadslink/     755 (rwxr-xr-x)
/var/log/jadslink/       755 (rwxr-xr-x)
```

---

## Flujo de Creación de Archivos en Runtime

### Primer inicio de sistema

```
[1] Boot OpenWrt
    ↓
[2] /etc/rc.local ejecuta:
    /usr/local/bin/jadslink-firewall-v2.sh
    ↓
    Crea: /etc/init.d/jadslink-session-cleanup
    ↓
[3] Directories creadas:
    /var/cache/jadslink/
    /var/log/jadslink/
    ↓
[4] Archivos iniciales:
    demo_tickets.db (manual - must be pre-created)
    used_codes.db (vacío, se crea al primer uso)
    sessions.db (vacío, se crea al primer uso)
    ↓
[5] Init service inicia:
    /etc/init.d/jadslink-session-cleanup start
    ↓
[6] Loop infinito comienza:
    Cada 60s: /usr/local/bin/session-cleanup.sh
    Genera: cleanup.log con ejecuciones
```

### Primer usuario se conecta

```
[1] Usuario ingresa código ABC123XYZ
    ↓
[2] CGI /www/cgi-bin/portal-api-v2.sh
    Escribe:
    - demo_tickets.db: Elimina ABC123XYZ
    - used_codes.db: Crea línea "ABC123XYZ:IP:TS"
    - sessions.db: Crea línea "SESSIONID:IP:..."
    - sessions.log: Append "[TS] Session=..."
    - used_codes.log: Append "[TS] Code=..."
    ↓
[3] 30 minutos después:
    Cleanup script se ejecuta
    Escribe:
    - sessions.db: Actualiza status a "expired"
    - expired_sessions.log: Append "[TS] ExpiredSession=..."
    - cleanup.log: Append log de ejecución
```

---

## Relaciones de Archivos

### demo_tickets.db ↔ used_codes.db

```
demo_tickets.db (origen):
ABC123XYZ:30
DEF456UVW:60

Usuario activa ABC123XYZ:

demo_tickets.db (después):
DEF456UVW:60         ← ABC123XYZ ELIMINADO

used_codes.db (registro):
ABC123XYZ:192.168.1.100:1714512345  ← AÑADIDO
```

### sessions.db ↔ cleanup.log

```
sessions.db:
a1b2c3d4:192.168.1.100:ABC123XYZ:1714512345:30:active

[60 segundos después]

cleanup.sh compara:
current_timestamp - 1714512345 = 1800+ segundos
duration_seconds = 30 * 60 = 1800 segundos
1800+ >= 1800 → EXPIRADO

sessions.db (después):
a1b2c3d4:192.168.1.100:ABC123XYZ:1714512345:30:expired
                                                    ↑
                                                    CAMBIO

cleanup.log (registro):
[2026-05-01 15:00:00] Cleanup executed
[2026-05-01 15:01:00] Cleanup executed
[...etc...]
```

---

## Archivos de Configuración (Existentes - Verificar)

Estos archivos ya deben existir en OpenWrt, pero necesitan verificación:

```
/etc/config/dhcp
├─ dnsmasq (debe escuchar :53)
├─ DHCP (debe servir 192.168.1.x)

/etc/config/uhttpd
├─ cgi_prefix = '/cgi-bin'
├─ Port 80 activo

/etc/config/network
├─ LAN IP = 192.168.1.1
├─ LAN Subnet = 255.255.255.0

/www/index.html
├─ Portal HTML (debe existir)
```

---

## Flujo de Datos en el Tiempo

```
TIMELINE:

T=0s: Usuario conecta a WiFi
      → DHCP asigna IP 192.168.1.100
      → DNS redirige captive.apple.com

T=5s: Usuario abre portal
      → Ve HTML, ingresa ABC123XYZ

T=6s: POST a /cgi-bin/portal-api-v2.sh
      ├─ demo_tickets.db: Elimina ABC123XYZ
      ├─ used_codes.db: ABC123XYZ:100:1234567890
      ├─ sessions.db: a1b2c3d:100:ABC123...:1234567890:30:active
      ├─ sessions.log: [TS] Session=a1b2c3d IP=100 Code=ABC123...
      └─ Firewall: Agrega regla nftables

T=6-1800s: Usuario tiene acceso
            ├─ Puede navegar a google.com ✓
            ├─ Puede navegar a facebook.com ✓
            └─ Cleanup.sh NO hace nada (sesión activa)

T=1800s: Cleanup.sh ejecuta (cada 60s, así que T=1800 sale 1 vez)
         ├─ Ve: current_time - created_at = 1800
         ├─ Ve: duration = 30 min = 1800 seg
         ├─ Detecta: EXPIRADA
         ├─ sessions.db: Cambia status a "expired"
         ├─ Firewall: Remueve regla
         └─ expired_sessions.log: Registra expiración

T=1800+s: Usuario intenta navegar
          ├─ Firewall: DROP (regla fue removida)
          ├─ Conexión rechazada
          └─ Portal reaparece

T=1800+30s: Usuario ve portal y puede ingresar código DIFERENTE
            ├─ ABC123XYZ: RECHAZADO (already in used_codes.db)
            ├─ DEF456UVW: ACEPTADO (exists in demo_tickets.db)
            └─ Proceso se repite
```

---

## Migración de v1 → v2

Si tienes v1 instalado:

```bash
# 1. Backup de v1
cp /www/cgi-bin/portal-api.sh /www/cgi-bin/portal-api.sh.bak
cp /var/cache/jadslink/demo_tickets.db /tmp/demo_tickets.db.bak

# 2. Instalar v2
scp openwrt-scripts/portal-api-v2.sh root@192.168.0.10:/www/cgi-bin/
scp openwrt-scripts/session-cleanup.sh root@192.168.0.10:/usr/local/bin/
scp openwrt-scripts/jadslink-session-cleanup.init root@192.168.0.10:/etc/init.d/
scp openwrt-scripts/jadslink-firewall-v2.sh root@192.168.0.10:/usr/local/bin/

# 3. Dar permisos
chmod 755 /www/cgi-bin/portal-api-v2.sh
chmod 755 /usr/local/bin/session-cleanup.sh
chmod 755 /etc/init.d/jadslink-session-cleanup
chmod 755 /usr/local/bin/jadslink-firewall-v2.sh

# 4. Eliminar archivo antiguo
rm /www/cgi-bin/portal-api.sh

# 5. Inicializar v2
/usr/local/bin/jadslink-firewall-v2.sh
/etc/init.d/jadslink-session-cleanup start
/etc/init.d/jadslink-session-cleanup enable

# 6. Verificar
ps aux | grep session-cleanup
nft list table inet jadslink
```

---

## Resumen Ejecutivo

| Categoría | Cantidad | Tamaño |
|-----------|----------|--------|
| **Scripts nuevos** | 4 | ~7.5 KB |
| **Archivos de datos** | 3+ | ~500-1000 B (per user) |
| **Archivos de logs** | 4 | Dynamic |
| **Directorios nuevos** | 2 | - |
| **Documentación** | 6 | ~50+ KB |

**Total footprint**: ~8-10 KB scripts + logs mínimos

---

## ✅ Checklist de Deployment

- [ ] Scripts copiados a OpenWrt
- [ ] Permisos dados (755 scripts, 644 datos)
- [ ] Directorios /var/cache/jadslink y /var/log/jadslink creados
- [ ] demo_tickets.db poblado con códigos
- [ ] Firewall inicializado
- [ ] Cleanup service activo
- [ ] dnsmasq redirigiendo DNS
- [ ] uhttpd con CGI habilitado
- [ ] /etc/rc.local ejecuta firewall en boot
- [ ] Logs se generan en /var/log/jadslink/

---

**Estructura finalizada**: 2026-05-01
**Versión**: 2.0
**Status**: ✅ LISTO PARA DEPLOYMENT
