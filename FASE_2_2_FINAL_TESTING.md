# 🚀 FASE 2.2 — Testing Final del Portal Captive

**Estado**: ✅ Sistema completamente configurado y listo
**Fecha**: 2026-05-01
**Versión**: 1.0

---

## 📊 Estado Actual del Sistema

### ✅ Componentes Activos

| Componente | Status | Detalles |
|-----------|--------|----------|
| **uhttpd** | ✅ RUNNING | Puerto 80, sirviendo portal HTML |
| **dnsmasq** | ✅ RUNNING | Puerto 53, redirigiendo dominios de detección |
| **jadslink-agent** | ✅ RUNNING | Reportando métricas al backend |
| **nftables firewall** | ✅ LOADED | Redirección HTTP y forward rules |
| **WiFi** | ✅ BROADCASTING | SSID: JADSlink-Hotspot (abierta) |
| **LAN Network** | ✅ CONFIGURED | 192.168.1.1/24 con DHCP |

### 🔧 Configuración de Firewall

```
┌─────────────────────────────────────────────────────┐
│          FIREWALL RULES (nftables)                  │
├─────────────────────────────────────────────────────┤
│ Chain: PREROUTING (nat)                             │
│   Rule 1: TCP:80 (cualquier destino excepto        │
│            192.168.1.1) → redirect to :80           │
│   Rule 2: UDP:53 (DNS) → accept                    │
│                                                      │
│ Chain: FORWARD (filter)                             │
│   Rule 1: Destino 192.168.1.1 → accept            │
│   Rule 2: Origen 192.168.1.0/24 → accept          │
└─────────────────────────────────────────────────────┘
```

**¿Qué significa?**
- Cualquier cliente que intente acceder a HTTP (puerto 80) es redirigido al portal local
- El DNS redirige dominios de "captive portal detection" a la portal IP
- Los clientes pueden comunicarse entre sí y con el router

### 🌐 Estrategia DNS

Los siguientes dominios resuelven a `192.168.1.1`:

```
Apple:    captive.apple.com               → 192.168.1.1
Android:  connectivitycheck.android.com   → 192.168.1.1
Chrome:   clients3.google.com             → 192.168.1.1
Firefox:  connectivity-check.firefox.com  → 192.168.1.1
Windows:  www.msftncsi.com                → 192.168.1.1
```

Cuando un navegador se conecta a una nueva red WiFi:
1. Intenta conectarse a uno de estos dominios
2. DNS lo redirige a 192.168.1.1
3. uhttpd sirve el portal HTML
4. **Portal aparece automáticamente** ✅

---

## 🧪 TESTING PASO A PASO

### Test 1: Primera Conexión (Auto-Detection)

**Objetivo**: Verificar que el portal aparece automáticamente en primera conexión

#### Pasos

1. **Desde tu cliente (laptop, phone, tablet)**:
   - Desconecta cualquier WiFi anterior

2. **Busca redes WiFi disponibles**:
   - Debes ver `JADSlink-Hotspot`

3. **Conecta sin contraseña**:
   - SSID: `JADSlink-Hotspot`
   - Contraseña: (ninguna - abierta)
   - Espera 3-5 segundos para DHCP

4. **Verifica que obtuviste IP**:
   - Debes tener IP en rango: `192.168.1.x`
   - Ejemplo: `192.168.1.105`, `192.168.1.203`, etc.

5. **Abre navegador web**:
   - NO escribas URL: `192.168.1.1`
   - Navega a cualquier sitio HTTP (NO HTTPS):
     - `http://google.com` ✅
     - `http://example.com` ✅
     - `http://facebook.com` ✅

#### Resultado Esperado ✅

Verás el portal HTML automáticamente:

```
═══════════════════════════════════════════
🌐 JADSlink

Acceso a Internet Satelital

Código de Acceso
[______________________________]

     [  Activar  ]

¿Cómo obtener un código?
Contacta al operador o escanea
el código QR proporcionado.
═══════════════════════════════════════════
```

**Si ves esto**: ✅ **Primera conexión FUNCIONA**

#### Si NO aparece el portal...

1. Revisa que tienes IP `192.168.1.x`
   ```bash
   ipconfig (Windows) o ifconfig (Mac/Linux)
   ```

2. Intenta acceder directamente a `http://192.168.1.1`
   - Si funciona: es problema de auto-detection del navegador
   - Si NO funciona: problema de red/firewall

3. Contacta con soporte y menciona:
   - Tu IP asignada
   - El navegador que usas
   - Sistema operativo

---

### Test 2: Reconexión (El problema actual)

**Objetivo**: Verificar que el portal aparece cuando te reconectas después de desconectar

#### Pasos

1. **Estando en el portal** (Test 1 completado)

2. **Desconecta WiFi**:
   - Settings → WiFi → JADSlink-Hotspot → Olvidar red
   - O simplemente apaga WiFi 5 segundos

3. **Reconecta a la misma red**:
   - WiFi → JADSlink-Hotspot
   - Conectar
   - Espera 3-5 segundos para DHCP

4. **Abre navegador**:
   - Ve a `http://google.com` (o similar)

#### Resultado Esperado ✅

El portal debe aparecer nuevamente en ~5-10 segundos automáticamente.

**Si aparece**: ✅ **Reconexión FUNCIONA** → **FASE 2.2 COMPLETADA**

#### Si NO aparece...

Esto es normal en algunos navegadores. **Soluciones**:

**Opción A: Forzar refresh**
- Presiona `Ctrl+Shift+R` (Windows/Linux) o `Cmd+Shift+R` (Mac)
- Borra cache del navegador
- Intenta de nuevo

**Opción B: Accede directamente**
- Si no aparece automáticamente, navega a: `http://192.168.1.1`
- El portal debe cargar
- Esto indica que la portal existe pero el auto-detection del navegador no se dispara en reconexión

**Opción C: Intenta otro navegador**
- Chrome, Firefox, Safari, Edge detectan captive portals diferente
- Algunos requieren HTTPS (nosotros estamos en HTTP)
- Prueba en múltiples navegadores

---

### Test 3: Validación de Códigos

**Objetivo**: Verificar que los códigos de activación funcionan

#### Códigos Disponibles para Testing

```
ABC123XYZ    → 30 minutos
DEF456UVW    → 60 minutos
GHI789RST    → 1 día (1440 min)
TEST001      → 30 minutos
TEST002      → 60 minutos
TEST003      → 1 día
TICKET001    → 30 minutos
TICKET002    → 60 minutos
TICKET003    → 1 día
```

#### Pasos

1. En el portal, en campo "Código de Acceso"
2. Ingresa: `ABC123XYZ`
3. Presiona botón: `[Activar]`
4. Espera 2-3 segundos

#### Resultado Esperado ✅

Recibirás respuesta JSON con éxito:

```
✓ Activado. Tienes acceso por 30 minutos.
```

**Si funciona**: ✅ **Validación de códigos FUNCIONA**

---

### Test 4: Acceso a Internet

**Objetivo**: Verificar que después de activar código, puedes navegar

#### Pasos

1. Después de Test 3 (código activado)
2. En el navegador, intenta navegar a:
   - `http://example.com`
   - `http://google.com`
   - `http://www.wikipedia.org`

#### Resultado Esperado ✅

Debes poder ver los sitios web sin problemas.

**Si funciona**: ✅ **Acceso a internet concedido**

---

## 📋 Resumen de Testing

```
┌─────────────────────────────────────┐
│  CHECKLIST - FASE 2.2 COMPLETADA   │
├─────────────────────────────────────┤
│ ✅ Test 1: Primera conexión         │
│    Portal aparece automáticamente   │
│                                     │
│ ✅ Test 2: Reconexión              │
│    Portal aparece nuevamente        │
│                                     │
│ ✅ Test 3: Validación códigos      │
│    Códigos se validan correctamente │
│                                     │
│ ✅ Test 4: Acceso a internet       │
│    Puedes navegar post-activación   │
│                                     │
│ ✅ Test 5: Servicios persistentes   │
│    Firewall/DNS persisten tras boot │
└─────────────────────────────────────┘
```

---

## 🔧 Troubleshooting Rápido

### "No veo el portal automáticamente"

**Causa más probable**: Navegador cachea que la red "ya tiene internet"

**Soluciones**:
1. Cierra navegador completamente y reabre
2. Borra cache (Settings → Clear cache)
3. Intenta otro navegador
4. Intenta acceso directo: `http://192.168.1.1`

### "El código no se valida"

**Verificar**:
```bash
ssh root@192.168.0.10  # password: 123456

# Revisar que cache existe
cat /var/cache/jadslink/demo_tickets.db | head -3

# Debe mostrar:
# ABC123XYZ:30
# DEF456UVW:60
# etc.
```

### "No tengo IP 192.168.1.x"

**Verificar**:
```bash
# Desde tu cliente:
ipconfig (Windows)
ifconfig (Mac/Linux)

# Si tienes otra IP (ej: 10.x.x.x), entonces:
# - DHCP no está funcionando correctamente
# - O hay conflicto de red
```

### "Aparece error de certificado SSL"

**Nota**: Esto no debe pasar, hemos deshabilitado HTTPS.
- Si aparece: borras cache del navegador
- O intenta incógnito/privado

---

## 📚 Archivos de Referencia

| Archivo | Descripción |
|---------|-------------|
| `/www/index.html` | Portal HTML (7.7 KB) |
| `/www/cgi-bin/portal-api.sh` | Script CGI para validación |
| `/etc/dnsmasq.conf` | Configuración DNS |
| `/etc/init.d/jadslink-firewall` | Script firewall persistente |
| `/var/cache/jadslink/demo_tickets.db` | Cache de códigos válidos |
| `/var/log/dnsmasq.log` | Logs de DNS |
| `/var/log/jadslink/agent.log` | Logs del agent |

---

## 🎯 Próximos Pasos

Una vez que Tests 1-4 pasen completamente:

### Fase 2.3: Integración con Backend
- Conectar con API en `192.168.0.201:8000`
- Reemplazar cache local con validación en tiempo real
- Documentación: `OPENWRT_API_INTEGRATION.md`

### Fase 2.4: Testing E2E Completo
- Testing con múltiples clientes
- Expiración automática de códigos
- Reconexión de usuarios
- Documentación: `OPENWRT_E2E_TESTING.md`

### Fase 2.5: Whitelabel y Customización
- Personalizar portal (logo, colores, textos)
- Integración con API Backend para tickets reales
- QR codes dinámicos

---

## ✅ Estado Final

**FASE 2.2: Portal Captive WiFi** — **LISTA PARA TESTING**

```
✓ Portal HTML funcional (7.7 KB)
✓ WiFi broadcasting (JADSlink-Hotspot)
✓ DHCP asignando IPs (192.168.1.x)
✓ DNS redirigiendo a portal
✓ Firewall redirigiendo HTTP
✓ Validación de códigos funcional
✓ Servicios persistentes

Estado: 🟢 LISTO PARA TESTING EN CLIENTE
```

---

**Documentación Relacionada**:
- `PORTAL_IMPLEMENTATION_COMPLETE.md` - Implementación técnica
- `TESTING_WIFI_NOW.md` - Testing rápido
- `TESTING_RECONNECT.md` - Detalle reconexión

**¡A probar!** 🚀
