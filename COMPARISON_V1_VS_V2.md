# 📊 Comparación: Versión 1 vs Versión 2

## Portal-API Script

### ❌ VERSIÓN 1 (Anterior)

```bash
#!/bin/sh
read POST_DATA
# Parse de parámetros simple
code=$(echo "$POST_DATA" | awk -F'[=&]' '{for(i=1;i<=NF;i++){if($i=="code")print $(i+1)}}')

# Validar código existe
if grep -q "^$code:" "$CACHE_FILE"; then
    DURATION=$(grep "^$code:" "$CACHE_FILE" | cut -d: -f2)

    # PROBLEMA 1: Código NO se elimina
    # ↓ MISMO código se puede usar varias veces

    # PROBLEMA 2: No hay session tracking
    # ↓ No se conoce cuándo expirar

    # PROBLEMA 3: IP se agrega al firewall
    # ↓ Pero nunca se remueve automáticamente

    json_response '{"success": true, "message": "✓ Activado..."}'
else
    json_response '{"success": false, "message": "Código no válido"}'
fi
```

**Problemas principales**:
1. ❌ Códigos reutilizables infinitamente
2. ❌ No hay expiración de sesiones
3. ❌ No hay logging de uso
4. ❌ Sin aislamiento entre clientes

---

### ✅ VERSIÓN 2 (Nueva)

```bash
#!/bin/sh

# NUEVAS CARACTERÍSTICAS 1-4:
USED_CODES_FILE="/var/cache/jadslink/used_codes.db"
SESSIONS_FILE="/var/cache/jadslink/sessions.db"

# 1. VALIDACIÓN: ¿Ya fue usado?
if grep -q "^$code:" "$USED_CODES_FILE" 2>/dev/null; then
    json_response '{"success": false, "message": "Código ya fue utilizado y expiró"}'
    exit 0
fi

# 2. VALIDACIÓN: ¿IP ya tiene sesión?
if grep -q "^[^:]*:$client_ip:" "$SESSIONS_FILE" 2>/dev/null; then
    if ... | grep -q ":active$"; then
        json_response '{"success": false, "message": "Este dispositivo ya tiene una sesión activa"}'
        exit 0
    fi
fi

# 3. SI VALIDACIÓN PASA: Generar Session ID único
SESSION_ID=$(generate_session_id "$client_ip" "$code")

# 4. ACCIONES POST-VALIDACIÓN:
# NUEVA: Eliminar código (one-time use)
sed -i "/^$code:/d" "$CODES_FILE"

# NUEVA: Registrar como usado
log_used_code "$code" "$client_ip"

# NUEVA: Crear sesión con expiración
log_session "$SESSION_ID" "$client_ip" "$code" "$DURATION"

# 5. RESPUESTA MEJORADA:
json_response '{"success": true, "message": "...", "session_id": "'$SESSION_ID'", "expires_in": '$((DURATION * 60))'}'
```

**Mejoras principales**:
1. ✅ Códigos se eliminan tras usar (one-time)
2. ✅ Session ID único para auditoría
3. ✅ Logging completo de uso
4. ✅ Prevención de múltiples sesiones por IP
5. ✅ Expiración calculada en respuesta

---

## Firewall Rules

### ❌ VERSIÓN 1 (HTTP Redirect)

```bash
# Problema: Firewall redirigía TODOS HTTP:80 a portal
# Esto causaba LOOP: usuario activaba → se redirigía a portal de nuevo

nft add rule inet jadslink prerouting tcp dport 80 \
    ip daddr != 192.168.1.1 redirect to :80

# Resultado: ❌ USUARIO EN LOOP INFINITO
```

**Problemas**:
- ❌ Loop infinito después de activar
- ❌ Usuario no puede navegar aunque tenga código válido
- ❌ Firewall no diferencia entre autenticado y no autenticado

---

### ✅ VERSIÓN 2 (DNS-based + Dynamic Rules)

```bash
# NUEVA ESTRATEGIA: No redirigir HTTP
# Solo confiar en DNS para detectar captive portal
# Usar firewall FORWARD para control real

# 1. ACEPTAR CONEXIONES ESTABLECIDAS (stateful)
nft add rule inet jadslink forward ct state established,related counter accept

# 2. PERMITIR ACCESO AL ROUTER MISMO (portal local)
nft add rule inet jadslink forward ip daddr 192.168.1.1 counter accept

# 3. PERMITIR COMUNICACIÓN DENTRO LAN
nft add rule inet jadslink forward ip daddr 192.168.1.0/24 counter accept

# 4. DEFAULT: BLOQUEAR LAN → WAN (previene acceso sin código)
nft add rule inet jadslink forward \
    ip saddr 192.168.1.0/24 ip daddr != 192.168.1.0/24 counter drop

# 5. DINÁMICO: Para cada IP autenticada, agregar regla ACCEPT
nft insert rule inet jadslink forward ip saddr 192.168.1.100 \
    ip daddr != 192.168.1.0/24 counter accept

# Resultado: ✅ Usuario puede navegar sin loop
```

**Mejoras**:
1. ✅ Sin loop - No redirige HTTP
2. ✅ Firewall verdaderamente default-deny
3. ✅ Reglas dinámicas por IP autenticada
4. ✅ Cleanup automático de reglas expired

---

## Session Management

### ❌ VERSIÓN 1 (Sin sesiones)

```
authenticated_ips.txt
─────────────────────
192.168.1.100

Problemas:
- No hay timestamp
- No hay duración
- No hay forma de expirar
- No hay logs de expiración
```

---

### ✅ VERSIÓN 2 (Session Management Completo)

```
sessions.db
──────────────────────────────────────────────
SESSION_ID:IP:CODE:TIMESTAMP:DURATION:STATUS
a1b2c3d4:192.168.1.100:ABC123XYZ:1714512345:30:active

used_codes.db
──────────────────────────────────
CODE:IP:TIMESTAMP
ABC123XYZ:192.168.1.100:1714512345

Características:
✅ Session ID único
✅ Timestamp para cálculo de expiración
✅ Duración en minutos
✅ Status (active/expired)
✅ Histórico de códigos usados
```

---

## Expiración de Sesiones

### ❌ VERSIÓN 1 (Sin expiración)

```
Usuario activa código a las 14:30:
- Obtiene acceso indefinido
- Sesión NUNCA expira
- Mismo código válido siempre
- Acceso permanente hasta logout manual
```

---

### ✅ VERSIÓN 2 (Expiración automática)

```
Usuario activa código a las 14:30 (duración: 30 min):
14:30 - Código eliminado de demo_tickets.db
14:30 - Sesión creada en sessions.db
14:30-15:00 - Usuario con acceso ✓
15:00 - session-cleanup.sh se ejecuta
        ↓ Detecta sesión expirada
        ↓ Remueve regla firewall
        ↓ Marca como "expired"
15:00+ - Usuario bloqueado, ve portal nuevamente ✗
```

**Ciclo**:
- Cleanup script corre cada 60 segundos
- Verifica todas las sesiones activas
- Si `elapsed_time >= duration`, expira
- Remueve regla nftables
- Registra en logs

---

## Logging y Auditoría

### ❌ VERSIÓN 1

```
Logs mínimos:
- Validación de código (sí/no)
- Poco detalle de quién, cuándo, cuánto tiempo
```

---

### ✅ VERSIÓN 2

```
sessions.log
────────────────────────────────────────────────────────
[2026-05-01 14:30:45] Session=a1b2c3d4 IP=192.168.1.100 Code=ABC123XYZ Duration=30
[2026-05-01 14:31:20] Session=x9y8z7w6 IP=192.168.1.101 Code=DEF456UVW Duration=60

used_codes.log
──────────────────────────────────────────────────────
[2026-05-01 14:30:45] Code=ABC123XYZ UsedBy=192.168.1.100
[2026-05-01 14:31:20] Code=DEF456UVW UsedBy=192.168.1.101

expired_sessions.log
──────────────────────────────────────────────────────────
[2026-05-01 15:00:45] ExpiredSession=a1b2c3d4 IP=192.168.1.100 Code=ABC123XYZ Duration=30
[2026-05-01 15:01:20] ExpiredSession=x9y8z7w6 IP=192.168.1.101 Code=DEF456UVW Duration=60

Auditoría completa:
✅ Quién (IP)
✅ Qué código
✅ Cuándo (timestamp)
✅ Cuánto tiempo (duración)
✅ Cuándo expiró
```

---

## Casos de Uso: Antes vs Después

### Caso 1: Reutilización de Código

**v1**:
```
Cliente A: ABC123XYZ ✓
Cliente B: ABC123XYZ ✓ (FUNCIONA)
Cliente C: ABC123XYZ ✓ (FUNCIONA)

Resultado: ❌ Un código = muchos usuarios
```

**v2**:
```
Cliente A: ABC123XYZ ✓ (primero en usar)
Cliente B: ABC123XYZ ✗ (rechazado - ya usado)
Cliente C: ABC123XYZ ✗ (rechazado - ya usado)

Resultado: ✅ Un código = un usuario
```

---

### Caso 2: Acceso Indefinido

**v1**:
```
Cliente A activa: ABC123XYZ (30 min)
14:30 - Obtiene acceso
14:45 - Sigue con acceso
15:00 - SIGUE CON ACCESO
16:00 - SIGUE CON ACCESO
...
Resultado: ❌ Duración no se respeta
```

**v2**:
```
Cliente A activa: ABC123XYZ (30 min)
14:30 - Obtiene acceso ✓
14:45 - Sigue con acceso ✓
15:00 - Cleanup marca como expired
        Firewall remueve regla
        Cliente BLOQUEADO ✗
15:00+ - Ve portal nuevamente, necesita nuevo código

Resultado: ✅ Duración respetada automáticamente
```

---

### Caso 3: Navegación Post-Activación

**v1**:
```
Cliente A activa código → Portal redirige HTTP → Usuario ve portal de nuevo
↓
Usuario: "¿Por qué volvió al portal?"
Resultado: ❌ LOOP INFINITO
```

**v2**:
```
Cliente A activa código → SIN redireccion HTTP → Usuario navega libremente
↓
Firewall: Solo bloquea tráfico SIN código (en FORWARD chain)
Usuario con código: Tráfico permitido en FORWARD
↓
Resultado: ✅ Usuario navega sin loop
```

---

## Tabla Comparativa

| Feature | v1 | v2 |
|---------|----|----|
| **Códigos one-time** | ❌ Reutilizable | ✅ Una sola vez |
| **Session tracking** | ❌ No | ✅ Sí (Session ID) |
| **Expiración automática** | ❌ No | ✅ Cada 60s |
| **Firewall rules cleanup** | ❌ Manual | ✅ Automático |
| **HTTP loop problem** | ❌ EXISTE | ✅ Resuelto |
| **Auditoría de uso** | ❌ Mínima | ✅ Completa |
| **Logs de expiración** | ❌ No | ✅ Sí |
| **Múltiples sesiones por IP** | ✅ Permitido | ❌ Bloqueado |
| **Código compartible** | ✅ Sí | ❌ No (una sola vez) |
| **Acceso indefinido** | ✅ Sí | ❌ Respeta duración |

---

## Diagrama de Flujo: Activación

### v1
```
Usuario ingresa código
    ↓
CGI valida: ¿existe?
    ↓ SÍ
Agrega IP al firewall
    ↓
Responde: "Activado"
    ↓
[FIN]

Problemas:
- Código sigue activo → puede usarse nuevamente
- Firewall rule permanente → acceso indefinido
```

### v2
```
Usuario ingresa código
    ↓
CGI valida: ¿existe?
    ├─ NO → Rechazar
    └─ SÍ → Continuar
CGI valida: ¿ya fue usado?
    ├─ SÍ → Rechazar ("Código ya utilizado")
    └─ NO → Continuar
CGI valida: ¿IP ya tiene sesión activa?
    ├─ SÍ → Rechazar ("Ya tiene sesión")
    └─ NO → Continuar
    ↓
ACCIONES:
1. Generar Session ID único
2. Eliminar código de demo_tickets.db
3. Registrar en used_codes.db
4. Crear sesión en sessions.db
5. Agregar regla firewall
6. Responder con session_id + expires_in
    ↓
[BACKGROUND] Cleanup task cada 60s:
- Verifica sesiones.db
- Detecta expiradas
- Remueve regla firewall
- Actualiza status a "expired"
    ↓
[FIN]

Mejoras:
✅ Código eliminado → imposible reutilizar
✅ Session tracking → sabe cuándo expiró
✅ Cleanup automático → respeta duración
✅ Auditoría completa → sabe quién, cuándo, por cuánto
```

---

## Impacto en Usuario Final

### Experiencia v1
```
✓ Primera conexión: Funciona
✓ Código válido: Obtiene acceso
✗ Después de activar: A veces loop
✗ Después de tiempo: Acceso indefinido
✗ Intenta reactivar: Funciona sin restricción
```

### Experiencia v2
```
✓ Primera conexión: Funciona
✓ Código válido: Obtiene acceso
✓ Después de activar: Navega sin loop
✓ Después de tiempo: Acceso revocado automáticamente
✓ Intenta reactivar: Código rechazado (ya usado)
✓ Usa código diferente: Nuevo acceso concedido
```

---

## Conclusión

**v2 implementa completamente los requisitos del usuario**:

1. ✅ Bloquea a todos (firewall default-deny)
2. ✅ Muestra portal a todos (DNS redirect)
3. ✅ Permite acceso a quienes entran código
4. ✅ **Código no reutilizable** (eliminado tras usar)
5. ✅ **Previene compartir internet** (session isolated)
6. ✅ **Expiración automática** (cleanup cada 60s)

**v1 vs v2**: La diferencia es la transformación de un sistema "permisivo" (todo permitido hasta que expire) a un sistema **"restrictivo"** (nada permitido hasta tener código válido + único).

---

**Implementación completada**: 2026-05-01
**Versión actual**: 2.0
**Estado**: ✅ LISTO PARA DEPLOYMENT
