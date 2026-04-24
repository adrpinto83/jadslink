# JADSlink Agent - OpenWrt Package

Este directorio contiene todo lo necesario para compilar e instalar el agente JADSlink como un paquete OpenWrt nativo (.ipk).

## Compatibilidad

- **Hardware**: GL.iNet GL-MT3000, y otros routers OpenWrt
- **Firmware**: OpenWrt 22.03+ (LEDE compatible)
- **Arquitectura**: ramips/mt7621, ar71xx, x86_64, etc.

## Requisitos para Compilación

1. OpenWrt SDK descargado para tu arquitectura
2. Dependencias: `build-essential`, `git`, `python3`
3. Espacio en disco: ~1GB

## Compilación del Package

### Opción 1: Dentro del SDK (Recomendado)

```bash
# 1. Descargar OpenWrt SDK para GL-MT3000
wget https://downloads.openwrt.org/releases/22.03.5/targets/ramips/mt7621/openwrt-sdk-22.03.5-ramips-mt7621_gcc-11.2.0_musl.Linux-x86_64.tar.xz

# 2. Extraer SDK
tar xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*/

# 3. Copiar el package de JADSlink
mkdir -p feeds/custom
cp -r /ruta/a/jadslink/openwrt-package feeds/custom/jadslink-agent

# 4. Actualizar feeds
./scripts/feeds update custom
./scripts/feeds install jadslink-agent

# 5. Compilar el package
make menuconfig
# Seleccionar: Network -> jadslink-agent
# Seleccionar: <*> (built-in) o <M> (module)

make package/feeds/custom/jadslink-agent/compile V=s

# 6. El .ipk estará en:
# bin/packages/mipsel_24kc/base/jadslink-agent_1.0.0-1_all.ipk
# (la arquitectura depende de tu hardware)
```

### Opción 2: Scripted Build

```bash
#!/bin/bash
set -e

SDK_URL="https://downloads.openwrt.org/releases/22.03.5/targets/ramips/mt7621/openwrt-sdk-22.03.5-ramips-mt7621_gcc-11.2.0_musl.Linux-x86_64.tar.xz"
JADSLINK_REPO="/ruta/a/jadslink"

# Descargar SDK
wget "$SDK_URL"
tar xf openwrt-sdk-*.tar.xz
cd openwrt-sdk-*/

# Setup feeds
mkdir -p feeds/custom
cp -r "$JADSLINK_REPO/openwrt-package" feeds/custom/jadslink-agent
./scripts/feeds update custom
./scripts/feeds install jadslink-agent

# Compilar
make package/feeds/custom/jadslink-agent/compile V=s

# Copiar resultado
mkdir -p /tmp/jadslink-ipk
cp bin/packages/*/base/jadslink-agent*.ipk /tmp/jadslink-ipk/

echo "Package compilado en /tmp/jadslink-ipk/"
```

## Instalación en el Router

### Transferencia del .ipk

```bash
# Desde la máquina de build
scp jadslink-agent_*.ipk root@192.168.8.1:/tmp/

# O desde el router, si tiene internet
ssh root@192.168.8.1
cd /tmp
wget https://releases.example.com/jadslink-agent_1.0.0-1_all.ipk
```

### Instalación

```bash
# En el router (SSH)
opkg update
opkg install /tmp/jadslink-agent_*.ipk

# Verificar instalación
opkg list-installed | grep jadslink
```

## Configuración

### Via UCI (Recomendado)

```bash
# SSH al router
ssh root@192.168.8.1

# Configurar parámetros requeridos
uci set jadslink.agent.node_id='YOUR_NODE_ID'
uci set jadslink.agent.api_key='YOUR_API_KEY'

# Configurar parámetros opcionales
uci set jadslink.agent.backend_url='https://api.jadslink.io'
uci set jadslink.agent.portal_port='80'
uci set jadslink.agent.max_bandwidth_mbps='100'

# Guardar cambios
uci commit jadslink

# Verificar configuración
uci show jadslink
```

### Via /etc/config/jadslink

```bash
cat /etc/config/jadslink
```

Editar directamente si es necesario:

```bash
vi /etc/config/jadslink
# Cambiar valores según sea necesario
# Luego reiniciar el servicio
/etc/init.d/jadslink restart
```

## Inicio del Servicio

```bash
# Iniciar manualmente
/etc/init.d/jadslink start

# Habilitar en boot
/etc/init.d/jadslink enable

# Verificar estado
/etc/init.d/jadslink status

# Ver logs en tiempo real
logread -f | grep jadslink

# Detener
/etc/init.d/jadslink stop
```

## Troubleshooting

### El servicio no inicia

```bash
# Ver error detallado
logread | grep jadslink | tail -20

# Verificar configuración
uci show jadslink.agent

# Verificar que NODE_ID y API_KEY están configurados
uci get jadslink.agent.node_id
uci get jadslink.agent.api_key
```

### Requiere que estén configurados ambos valores

```
ERROR: Missing required configuration: node_id, api_key
Configure with: uci set jadslink.agent.node_id=YOUR_NODE_ID
```

### Portal no accesible

```bash
# Verificar que el servicio está corriendo
ps aux | grep python3

# Verificar puerto (por defecto 80)
netstat -tlnp | grep 80

# Verificar reglas firewall
iptables -t nat -L JADSLINK_PREROUTING -n
iptables -t filter -L JADSLINK_FORWARD -n
```

### Alto consumo de RAM o CPU

```bash
# Monitorear en tiempo real
top

# El agent debe usar:
# RAM: < 25MB
# CPU (idle): < 5%

# Si excede:
# 1. Verificar configuración
# 2. Revisar logs
# 3. Reportar en GitHub
```

## Desinstalación

```bash
# Detener el servicio
/etc/init.d/jadslink stop

# Desinstalar package
opkg remove jadslink-agent

# Limpiar datos locales (opcional)
rm -rf /var/lib/jadslink
rm -rf /etc/config/jadslink
```

## Dependencias del Package

El package `.ipk` automáticamente instala:

- `python3` - Intérprete Python
- `python3-requests` - HTTP client
- `python3-schedule` - Task scheduling
- `tc` - Traffic control (QoS)
- `kmod-ifb` - Intermediate Functional Block
- `kmod-sched-core` - Kernel scheduling
- `kmod-sched-htb` - HTB qdisc
- `iptables-mod-conntrack-extra` - Iptables extensions

**Tamaño total**: ~8-10 MB

## Desarrollo

### Estructura del Package

```
openwrt-package/
├── Makefile                          # Instrucciones de build
├── files/
│   ├── etc/
│   │   ├── init.d/
│   │   │   └── jadslink              # OpenWrt init script
│   │   └── config/
│   │       └── jadslink              # UCI configuration
│   └── usr/
│       ├── bin/
│       │   └── jadslink-agent        # Entry point principal
│       └── lib/
│           └── jadslink/
│               ├── agent.py
│               ├── firewall.py
│               ├── config.py
│               ├── session_manager.py
│               ├── portal.py
│               ├── cache.py
│               ├── sync.py
│               └── ...
└── README.md                          # Este archivo
```

### Modificar el Package

Si necesitas hacer cambios:

1. Editar archivos en `files/`
2. Compilar nuevamente: `make package/feeds/custom/jadslink-agent/compile V=s`
3. Instalar en router: `opkg install /tmp/jadslink-agent*.ipk`

## Versioning y Updates

El package sigue versionado semántico:

- `1.0.0` - Release inicial
- Bugfixes: `1.0.1`, `1.0.2`, etc.
- Features: `1.1.0`, `1.2.0`, etc.
- Breaking changes: `2.0.0`

### Actualizar a nueva versión

```bash
# Descargar nuevo .ipk
scp /tmp/jadslink-agent_1.0.1-1_all.ipk root@192.168.8.1:/tmp/

# Instalar (sobrescribe versión anterior)
opkg install /tmp/jadslink-agent_1.0.1-1_all.ipk

# Verificar
opkg list-installed | grep jadslink
```

## Support y Reportar Issues

- **Documentación**: https://github.com/adrpinto83/jadslink
- **Issues**: https://github.com/adrpinto83/jadslink/issues
- **Email**: info@jads.studio

## Licencia

Proprietary - Uso interno JADS Studio

---

**Última actualización**: 2026-04-24
**Versión**: 1.0.0
**Compatible con**: OpenWrt 22.03+, GL-MT3000, y otros dispositivos
