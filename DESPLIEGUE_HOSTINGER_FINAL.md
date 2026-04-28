# 🚀 Despliegue JADSlink en Hostinger - Guía Final

**Fecha**: 2026-04-27
**Versión**: 2.0 (MySQL)
**Estado**: ✅ Listo para desplegar

---

## 📊 Resumen de Cambios Realizados

### ✅ JADSlink Adaptado para Hostinger+MySQL

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Base de datos** | PostgreSQL | MySQL/MariaDB ✅ |
| **Driver** | asyncpg | aiomysql ✅ |
| **Conexión** | postgresql+asyncpg:// | mysql+aiomysql:// ✅ |
| **Pool** | NullPool | QueuePool con MySQL ✅ |
| **Compatibilidad** | Solo PostgreSQL | Solo MySQL ✅ |
| **Funcionalidad** | 100% | 100% ✅ |

### 📦 Nuevo Archivo de Deploy

```
jadslink-deploy-mysql.tar.gz (508 KB)
├── api/                    → Backend FastAPI (ahora con MySQL)
├── dashboard/              → Frontend React
├── agent/                  → Field nodes
├── HOSTINGER_MYSQL_SETUP.md → Guía detallada
└── INICIO_RAPIDO_MYSQL.md  → Guía rápida
```

---

## 🎯 Próximos Pasos (10 minutos)

### 1️⃣ Descargar Archivo

**Ubicación local:**
```
/home/adrpinto/jadslink/jadslink-deploy-mysql.tar.gz
```

### 2️⃣ Subir a Hostinger

**Opción A: File Manager (Más fácil)**
- Panel Hostinger → File Manager
- Navega a `/home/u938946830/`
- Click "Upload" → Selecciona `jadslink-deploy-mysql.tar.gz`
- Click derecho → "Extract"

**Opción B: SCP (Desde terminal)**
```bash
scp -P 65002 jadslink-deploy-mysql.tar.gz u938946830@217.65.147.159:/home/u938946830/
```

### 3️⃣ En Hostinger (por SSH)

```bash
ssh -p 65002 u938946830@217.65.147.159
cd jadslink-deploy
cp api/.env.hostinger .env
nano .env
# ↓ Editar DATABASE_URL con credenciales de BD de Hostinger
```

**Formato DATABASE_URL:**
```bash
mysql+aiomysql://usuario:contraseña@localhost:3306/basedatos

# Ejemplo:
mysql+aiomysql://u938946830_jadslink:micontraseña@localhost:3306/u938946830_jadslink
```

### 4️⃣ Instalar

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Migraciones
alembic upgrade head

# Datos demo (opcional)
python3 scripts/reset_and_seed.py
```

### 5️⃣ Ejecutar

```bash
# Opción 1: PM2 (recomendado)
npm install -g pm2
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name jadslink-api

# Opción 2: Directo (prueba)
gunicorn -w 4 -b 127.0.0.1:8000 main:app
```

### 6️⃣ Acceder

```
https://wheat-pigeon-347024.hostingersite.com
Demo: demo@jadslink.com / demo123456
```

---

## 🔐 Obtener Credenciales de BD en Hostinger

**Panel Hostinger:**
1. Login a tu cuenta
2. Ir a → **Bases de Datos** (o MySQL)
3. Buscar tu base de datos

**Datos que necesitas:**
- Host: `localhost`
- Puerto: `3306`
- Usuario: `u938946830_...` (algo así)
- Contraseña: (generada por Hostinger)
- BD: (nombre de la base de datos)

**Formato final en .env:**
```bash
DATABASE_URL=mysql+aiomysql://USUARIO:CONTRASEÑA@localhost:3306/BD
```

---

## 📋 Checklist de Instalación

- [ ] Archivo `jadslink-deploy-mysql.tar.gz` descargado
- [ ] Archivo subido a Hostinger
- [ ] Archivo extraído en `/home/u938946830/jadslink-deploy`
- [ ] Credenciales de BD obtenidas de Hostinger
- [ ] Archivo `.env` configurado con DATABASE_URL
- [ ] Claves secretas generadas (SECRET_KEY, TICKET_HMAC_SECRET)
- [ ] Virtual environment creado
- [ ] Dependencias instaladas
- [ ] Migraciones ejecutadas (`alembic upgrade head`)
- [ ] API corriendo (PM2 o gunicorn)
- [ ] Nginx configurado en panel Hostinger
- [ ] Dashboard compilado (opcional)
- [ ] Acceso a https://wheat-pigeon-347024.hostingersite.com ✅

---

## 📚 Documentación Disponible

Dentro del archivo TAR.GZ:

1. **HOSTINGER_MYSQL_SETUP.md** (⭐ PRINCIPAL)
   - Guía paso a paso completa
   - Solución de problemas detallada
   - Comandos exactos a ejecutar

2. **INICIO_RAPIDO_MYSQL.md**
   - Versión super simplificada
   - Solo los pasos esenciales

3. **CLAUDR.md**
   - Arquitectura del proyecto
   - Descripción técnica

---

## 🆘 Problemas Comunes

### "Cannot connect to database"
```bash
# Verificar que la BD existe en Hostinger
mysql -h localhost -u tu_usuario -p

# Ver DATABASE_URL en .env
cat .env | grep DATABASE_URL
```

### "ModuleNotFoundError"
```bash
source venv/bin/activate
pip install aiomysql fastapi sqlalchemy
```

### "Port 8000 in use"
```bash
# Matar proceso
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### "502 Bad Gateway"
- Verifica que API está corriendo: `pm2 status`
- Verifica logs: `pm2 logs jadslink-api`
- Nginx proxy reverso puede estar mal configurado

---

## 📞 Soporte

**Si algo falla:**

1. **Lee primero**: `HOSTINGER_MYSQL_SETUP.md` → Sección "Troubleshooting"
2. **Verifica logs**: `pm2 logs jadslink-api`
3. **Conecta BD**: `mysql -u usuario -p basedatos`
4. **Test API**: `curl -s http://localhost:8000/health`

---

## ✅ Resultado Esperado

Después de completar todos los pasos:

```
✅ API en: https://wheat-pigeon-347024.hostingersite.com/api/health
✅ Dashboard en: https://wheat-pigeon-347024.hostingersite.com
✅ BD: MySQL/MariaDB conectada
✅ Usuarios: Funcionando
✅ Sesiones: Funcionando
✅ Seguridad: HTTPS
```

---

## 🎯 Próximas Mejoras (Futuro)

Después de que el sistema esté corriendo:

1. **Crear primer operador** en Admin Panel
2. **Configurar Stripe** (opcional)
3. **Configurar Email** (opcional)
4. **Monitoreo**: `pm2 monit` o `pm2 logs`
5. **Backups**: Configurar en Hostinger

---

## 📊 Estructura Final en Hostinger

```
/home/u938946830/
├── jadslink-deploy/          ← Tu proyecto
│   ├── api/
│   │   ├── venv/            ← Virtual environment Python
│   │   ├── .env             ← Configuración (NO commitar)
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routers/
│   │   └── requirements.txt
│   ├── dashboard/
│   │   ├── dist/            ← Build compilado
│   │   └── package.json
│   ├── agent/
│   └── docs/
│
├── .env.hostinger           ← Template (referencia)
└── HOSTINGER_MYSQL_SETUP.md ← Guía
```

---

## 🚀 Comando Rápido de Instalación

**Si ya tienes Hostinger listo:**

```bash
# 1. Conectar
ssh -p 65002 u938946830@217.65.147.159

# 2. Extraer
tar -xzf jadslink-deploy-mysql.tar.gz
cd jadslink-deploy

# 3. Configurar
cp api/.env.hostinger .env
nano .env
# ↓ Editar DATABASE_URL y claves

# 4. Instalar
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Migraciones
alembic upgrade head
python3 scripts/reset_and_seed.py

# 6. Ejecutar
npm install -g pm2
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name jadslink-api

# 7. Acceder
# https://wheat-pigeon-347024.hostingersite.com
```

---

**¡Sistema listo para producción! 🎉**

**Última actualización**: 2026-04-27
**Versión**: 2.0 (MySQL adaptado para Hostinger)
**Status**: ✅ Listo
