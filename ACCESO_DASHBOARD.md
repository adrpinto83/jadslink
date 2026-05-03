# Guía de Acceso al Dashboard - 3 de Mayo, 2026

## Estado Verificado ✅

- ✅ Nginx está corriendo en puerto 3000 (dentro del contenedor)
- ✅ Docker ha mapeado puerto 3000 del host → puerto 80 del contenedor
- ✅ HTML del dashboard se está sirviendo correctamente
- ✅ API está respondiendo en puerto 8000

## URLs de Acceso

### Desde el Servidor (192.168.0.201)

| Servicio | URL | Estado |
|----------|-----|--------|
| Dashboard | `http://localhost:3000` | ✅ Funciona |
| API | `http://localhost:8000` | ✅ Funciona |
| API Docs | `http://localhost:8000/docs` | ✅ Funciona |

### Desde tu PC (192.168.0.159)

| Servicio | URL | Esperado |
|----------|-----|----------|
| Dashboard | `http://192.168.0.201:3000` | Debería funcionar |
| API | `http://192.168.0.201:8000` | Debería funcionar |
| API Docs | `http://192.168.0.201:8000/docs` | Debería funcionar |

## Troubleshooting - Si No Puedes Acceder

### Paso 1: Verificar Conectividad Básica
Desde tu PC (192.168.0.159), abre PowerShell/Terminal y ejecuta:

```bash
# Verificar ping al servidor
ping 192.168.0.201

# Debe responder: Reply from 192.168.0.201: bytes=32 time=...
```

**Si el ping falla:**
- El servidor no es accesible desde tu red
- Verifica que ambas máquinas están en la misma red local
- Comprueba el firewall del servidor

### Paso 2: Verificar Puertos TCP Abiertos
Desde tu PC, ejecuta:

```bash
# Windows (PowerShell)
Test-NetConnection -ComputerName 192.168.0.201 -Port 3000
Test-NetConnection -ComputerName 192.168.0.201 -Port 8000

# Linux/Mac
nc -zv 192.168.0.201 3000
nc -zv 192.168.0.201 8000
```

**Si no abre conexión:**
- El firewall está bloqueando los puertos
- Necesitas abrir los puertos en el firewall del servidor
- O cambiar a modo bridge si está en Proxmox LXC

### Paso 3: Acceder al Dashboard
Una vez confirmada la conectividad:

1. **Abre tu navegador**
2. **Escribe en la barra de direcciones:**
   ```
   http://192.168.0.201:3000
   ```
3. **Presiona Enter**

Deberías ver la página del dashboard de JADSlink.

## Instrucciones para Acceder en Proxmox

Si estás en Proxmox (192.168.0.200) y el contenedor (192.168.0.201) está aislado:

### Opción 1: SSH Tunnel
```bash
# Desde tu PC, hacer un túnel SSH al servidor Proxmox
ssh -L 3000:192.168.0.201:3000 root@192.168.0.200

# Luego accede en tu navegador:
# http://localhost:3000
```

### Opción 2: Configurar Bridge en Proxmox
Si el contenedor está en NAT:
1. En Proxmox, editar la configuración de red del contenedor 201
2. Cambiar interfaz de red a `vmbr0` (bridge) o similar
3. Esperar a que obtenga IP en la red local
4. Luego accede a `http://192.168.0.201:3000`

### Opción 3: Port Forward en OpenWrt
Si OpenWrt (192.168.0.10) está haciendo NAT:
```bash
# Agregar regla de port forward en OpenWrt
uci add firewall rule
uci set firewall.@rule[-1].src=wan
uci set firewall.@rule[-1].dst=lan
uci set firewall.@rule[-1].dest_port=3000
uci set firewall.@rule[-1].target=DNAT
uci set firewall.@rule[-1].proto=tcp
uci set firewall.@rule[-1].dest_ip=192.168.0.201
uci set firewall.@rule[-1].dest_port=3000
uci commit firewall
/etc/init.d/firewall restart
```

## Problema: "Unsafe attempt to load URL"

Este error de Chrome significa:
- ✅ Chrome intentó conectar a la URL
- ❌ Pero recibió una página de error del navegador
- Probablemente DNS no resuelve, o no hay conectividad TCP

**Solución:**
1. Verifica ping a 192.168.0.201 (Paso 1 arriba)
2. Verifica puerto 3000 abierto (Paso 2 arriba)
3. Si ambos funcionan, intenta en otra pestaña nueva
4. Si persiste, intenta limpiar caché: Ctrl+Shift+Del

## Dashboard ya Funciona

Confirmado en el servidor:
```bash
curl -I http://localhost:3000/
# HTTP/1.1 200 OK
# Content-Type: text/html
```

El HTML se está sirviendo correctamente. Solo necesitas accesibilidad de red desde tu PC.

## Próximos Pasos Después de Acceder

1. Verifica que ves la página de login del dashboard
2. Intenta login con:
   - Email: `operator@demo.com`
   - Password: `123456`
3. Si no funciona, es el error 500 del backend que estamos debuggeando
4. Reporta qué ves para continuar

## Contacto / Debug

Si tienes problemas:
1. Comparte el resultado de `ping 192.168.0.201` desde tu PC
2. Comparte el resultado de `Test-NetConnection -ComputerName 192.168.0.201 -Port 3000` (Windows)
3. Comparte qué URL exactamente escribiste en el navegador
4. Comparte si ves algún mensaje de error específico
