# Acceso al Dashboard - Soluciones Alternativas

## Problema Identificado

- ✅ El dashboard está corriendo en el servidor (172.21.204.29:3000)
- ✅ Conectividad básica existe (ping funciona a 192.168.0.201)
- ❌ El puerto TCP 3000 no es accesible desde tu PC (probablemente firewall de Proxmox)

## Solución 1: SSH Tunneling (Recomendado)

Esta es la forma más rápida de acceder mientras Proxmox está configurando los puertos.

### En Windows (PowerShell)

```powershell
# Conectar a través de SSH tunneling
ssh -L 3000:172.21.204.29:3000 -L 8000:172.21.204.29:8000 root@192.168.0.201

# Luego abre en tu navegador:
# http://localhost:3000
```

**Credenciales SSH:**
- Usuario: `root`
- IP: `192.168.0.201`
- Puerto: 22 (por defecto)

### En Mac/Linux

```bash
ssh -L 3000:172.21.204.29:3000 -L 8000:172.21.204.29:8000 root@192.168.0.201
```

Luego accede a:
```
http://localhost:3000
```

## Solución 2: Acceder Directamente Dentro de Proxmox

Si tienes acceso a una consola o terminal dentro del contenedor:

```bash
# Desde dentro del contenedor
curl http://localhost:3000

# O abre Firefox/navegador dentro del contenedor y ve a:
# http://localhost:3000
```

## Solución 3: Configurar Proxmox Port Forwarding (Largo Plazo)

Si quieres acceso permanente sin SSH tunnel, necesitas configurar port forwarding en Proxmox.

**En Proxmox (192.168.0.200):**

1. Abre terminal de Proxmox
2. Edita `/etc/pve/containers/201.conf` (reemplaza 201 con tu ID de contenedor)
3. Agrega estas líneas:

```
mp0: /mnt/pve/local,mp=/mnt/pve
# Port forwarding rules
rpcbind: 0
```

O usa reglas de firewall en Proxmox:

```bash
# SSH al Proxmox
ssh root@192.168.0.200

# Crear rules de port forward
iptables -t nat -A PREROUTING -p tcp --dport 3000 -j DNAT --to-destination 172.21.204.29:3000
iptables -t nat -A POSTROUTING -j MASQUERADE

# Guardar reglas (depende del sistema)
iptables-save > /etc/iptables.rules
```

## Solución 4: Usar IP Directa del Contenedor

Si configuras DNS en tu PC para resolver `192.168.0.201` → `172.21.204.29`:

```powershell
# En Windows hosts file: C:\Windows\System32\drivers\etc\hosts
# Agregar línea:
172.21.204.29   jadslink.local

# Luego acceder a:
# http://jadslink.local:3000
```

## Verificar Qué IP Está Activa

Desde Proxmox, ejecuta:

```bash
# Ver información del contenedor
pct exec 201 -- ip addr

# Verás algo como:
# inet 172.21.204.29/20 brd 172.21.207.255 scope global eth0
```

La IP `172.21.204.29` es la dirección real del contenedor Docker.

## Próximos Pasos

### Opción Inmediata (Hoy)
Usa **SSH Tunneling** para acceder ahora mientras debuggeamos Proxmox.

### Opción Permanente
Contacta al administrador de Proxmox para abrir los puertos 3000 y 8000, o configura port forwarding como se describe arriba.

## Credenciales de Prueba

Una vez accedas al dashboard:

```
Email:    operator@demo.com
Password: 123456
```

---

**Nota**: El problema actual es específico de la configuración de red de Proxmox. Los servicios Docker están funcionando correctamente en la dirección IP real del contenedor (172.21.204.29).
