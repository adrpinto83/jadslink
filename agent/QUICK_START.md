# 🚀 JADSlink OpenWrt - Quick Start

**Tiempo de lectura**: 2 minutos
**Tiempo de setup**: 5-10 minutos

---

## 1️⃣ Antes de Empezar

Asegúrate de tener:

- ✅ JADSlink corriendo: `docker compose ps` 
- ✅ Nodo creado en Dashboard (NODE_ID + API_KEY)
- ✅ OpenWrt encendido y en la red (10.0.0.1 o 192.168.0.X)
- ✅ SSH habilitado en OpenWrt

---

## 2️⃣ Opción A: Asistente Automático ⭐ (Recomendado)

```bash
cd /home/adrpinto/jadslink/agent
python3 setup-wizard.py
```

El wizard te guiará paso a paso. Toma ~5-10 minutos.

**Qué hace**:
1. ✓ Valida tu setup local
2. ✓ Conecta a OpenWrt
3. ✓ Recopila credenciales
4. ✓ Despliega automáticamente
5. ✓ Inicia el servicio
6. ✓ Muestra instrucciones finales

---

## 3️⃣ Opción B: Manual Rápido

```bash
# 1. Validar
python3 validate-setup.py

# 2. Desplegar
bash deploy-to-openwrt.sh 10.0.0.1

# 3. Testear
bash test-openwrt.sh 10.0.0.1

# 4. Iniciar (vía SSH)
ssh root@10.0.0.1 '/etc/init.d/jadslink start'
```

---

## 4️⃣ Verificar que Funciona

### En 30 segundos...

1. Ve a **Dashboard → Nodos**
2. Tu nodo debe mostrar estado **"online"** ✅

### En 5 minutos...

1. Conecta un móvil a WiFi **"JADSlink-WiFi"**
2. Abre navegador → google.com
3. Deberías ver el **portal captive**
4. Ingresa un **código de ticket** del dashboard
5. ✓ Deberías tener internet

---

## 5️⃣ Comandos Útiles

```bash
# Ver logs del agente
ssh root@10.0.0.1 'logread -f | grep jadslink'

# Ver estado
ssh root@10.0.0.1 'ps | grep agent.py'

# Reiniciar
ssh root@10.0.0.1 '/etc/init.d/jadslink restart'

# Ver configuración
ssh root@10.0.0.1 'cat /opt/jadslink/.env'
```

---

## 6️⃣ Documentación Completa

| Archivo | Propósito |
|---------|----------|
| `OPENWRT_SETUP.md` | Guía detallada con troubleshooting |
| `validate-setup.py` | Validación pre-setup |
| `setup-wizard.py` | Asistente interactivo |
| `deploy-to-openwrt.sh` | Despliegue de archivos |
| `test-openwrt.sh` | Testing post-deploy |

---

## ❓ Si Hay Problemas

**Nodo no aparece online**:
```bash
ssh root@10.0.0.1 'logread | grep -i error'
```

**Portal no redirige**:
```bash
ssh root@10.0.0.1 'netstat -tlnp | grep :80'
```

**Más ayuda**:
- Ver: `OPENWRT_SETUP.md` → Troubleshooting
- O: `OPENWRT_IMPLEMENTATION_SUMMARY.md`

---

**¡Listo!** 🎉

Tu nodo OpenWrt está configurado como nodo JADSlink.

Para los próximos pasos, ve a: `OPENWRT_SETUP.md`
