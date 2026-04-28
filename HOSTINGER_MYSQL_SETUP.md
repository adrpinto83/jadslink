# 🚀 JADSlink en Hostinger con MySQL

**Fecha**: 2026-04-27
**Ambiente**: Hostinger Shared Hosting con MySQL/MariaDB
**Dominio**: wheat-pigeon-347024.hostingersite.com
**Usuario**: u938946830

---

## ⚠️ Cambio Importante

JADSlink ha sido **adaptado para funcionar con MySQL/MariaDB** en lugar de PostgreSQL, ya que Hostinger en este plan solo proporciona MySQL.

**Lo que cambió:**
- ✅ Driver de BD: `asyncpg` → `aiomysql`
- ✅ Cadena conexión: `postgresql+asyncpg://` → `mysql+aiomysql://`
- ✅ Configuración: Optimizada para MySQL
- ✅ Todas las migraciones funcionan igual

**Lo que NO cambió:**
- ✅ Modelos de datos (mismo schema)
- ✅ API endpoints
- ✅ Frontend
- ✅ Funcionalidad

---

## 📋 Prerequisitos

- Acceso SSH a Hostinger (provided)
- Python 3.9+
- MySQL/MariaDB (ya disponible en Hostinger)
- 500MB espacio libre

---

## 🔧 Paso 1: Obtener Credenciales de BD en Hostinger

### En Panel Hostinger

1. **Login**: https://hostinger.com/account
2. **Ir a**: Bases de Datos (o MySQL)
3. **Buscar tu BD** o crear una nueva

   | Campo | Valor |
   |-------|-------|
   | **Nombre BD** | Probablemente `u938946830_jadslink` |
   | **Usuario** | Probablemente `u938946830_jadslink` |
   | **Contraseña** | (la que generó Hostinger) |
   | **Host** | `localhost` |
   | **Puerto** | `3306` |

4. **Guardar estas credenciales** (las necesitarás en el .env)

---

## 📤 Paso 2: Subir Archivos a Hostinger

### Opción A: File Manager (Recomendado)

1. Panel Hostinger → **File Manager**
2. Navega a `/home/u938946830/`
3. Click **"Upload"** → Selecciona `jadslink-deploy-mysql.tar.gz`
4. Click derecho → **"Extract"**

### Opción B: SCP/Terminal

```bash
# Desde tu máquina local
scp -P 65002 jadslink-deploy-mysql.tar.gz u938946830@217.65.147.159:/home/u938946830/
```

---

## 🔐 Paso 3: Configurar Variables de Entorno

### Conectar por SSH

```bash
ssh -p 65002 u938946830@217.65.147.159
cd jadslink-deploy
```

### Copiar Template

```bash
cp api/.env.hostinger .env
```

### Editar .env

```bash
nano .env
```

### Actualizar Credenciales de BD

Busca esta línea:

```bash
DATABASE_URL=mysql+aiomysql://u938946830_jadslink:TU_CONTRASEÑA@localhost:3306/u938946830_jadslink
```

**Reemplaza:**
- `u938946830_jadslink` → Tu usuario de BD (si es diferente)
- `TU_CONTRASEÑA` → Tu contraseña de BD
- `u938946830_jadslink` → Nombre de tu BD (si es diferente)

**Ejemplo real:**
```bash
DATABASE_URL=mysql+aiomysql://u938946830_lineair:Amore230617*@localhost:3306/u938946830_lineair
```

### Generar Claves Seguras

```bash
# Genera dos claves (cópialas en el .env)
python3 -c "import secrets; print(secrets.token_hex(32))"
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Actualiza en el .env:
```bash
SECRET_KEY=CLAVE_1_GENERADA
TICKET_HMAC_SECRET=CLAVE_2_GENERADA
```

### Guardar Archivo

1. `Ctrl + O`
2. `Enter`
3. `Ctrl + X`

---

## 📦 Paso 4: Instalar Dependencias

```bash
cd /home/u938946830/jadslink-deploy/api

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias (ahora con aiomysql para MySQL)
pip install -r requirements.txt
```

**Verificar instalación:**
```bash
python3 -c "import aiomysql; print('✅ aiomysql OK')"
python3 -c "import fastapi; print('✅ FastAPI OK')"
```

---

## 🗄️ Paso 5: Crear Tablas (Migraciones)

```bash
# Asegúrate que venv está activado
source venv/bin/activate

# Ejecutar migraciones
alembic upgrade head
```

**Output esperado:**
```
INFO  [alembic.runtime.migration] Running upgrade → [migration1]
INFO  [alembic.runtime.migration] Running upgrade [migration1] → [migration2]
...
✅ Base de datos actualizada
```

---

## 🌱 Paso 6: Aplicar Seed de Datos (Opcional)

```bash
python3 scripts/reset_and_seed.py
```

**Output esperado:**
```
✅ Base de datos limpia
✅ Tablas creadas
✅ SEED COMPLETADO EXITOSAMENTE

CREDENCIALES DE ACCESO:
DEMO: demo@jadslink.com / demo123456
ADMIN: admin@jads.com / admin123456
```

---

## 🚀 Paso 7: Levantar API

### Opción A: PM2 (Recomendado)

```bash
# Instalar PM2
npm install -g pm2

# Desde /home/u938946830/jadslink-deploy/api (con venv activado)
source venv/bin/activate
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name jadslink-api

# Verificar estado
pm2 status
pm2 logs jadslink-api
```

### Opción B: Directamente con Gunicorn (Prueba)

```bash
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 main:app
```

---

## ⚙️ Paso 8: Configurar Nginx en Panel Hostinger

1. Panel Hostinger → **Sitios Web**
2. Click en `wheat-pigeon-347024.hostingersite.com`
3. **Configuración Avanzada** → **Proxy Reverso** (o similar)

**Configuración:**

```
Destino: http://127.0.0.1:8000
```

O si necesitas configuración Nginx manual:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location / {
    alias /home/u938946830/jadslink-deploy/dashboard/dist/;
    try_files $uri $uri/ /index.html;
}
```

---

## 🎨 Paso 9: Compilar Dashboard (Opcional)

```bash
cd /home/u938946830/jadslink-deploy/dashboard

npm install
npm run build
```

---

## ✅ Paso 10: Verificar que Funcione

```bash
# Health check
curl -s http://localhost:8000/health | head -20

# Debe responder:
# {"status":"healthy","checks":{"database":"ok"}}
```

**Desde navegador:**
```
https://wheat-pigeon-347024.hostingersite.com
```

**Login demo:**
- Email: `demo@jadslink.com`
- Contraseña: `demo123456`

---

## 🐛 Troubleshooting

### Error: "Cannot connect to database"

```bash
# Verificar credenciales
mysql -h localhost -u u938946830_jadslink -p

# Si falla, verifica:
# 1. DATABASE_URL en .env es correcto
# 2. Usuario y contraseña son correctos
# 3. Base de datos existe
```

### Error: "aiomysql not found"

```bash
source venv/bin/activate
pip install aiomysql
```

### Error: "Port 8000 in use"

```bash
# Matar proceso anterior
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# O cambiar puerto
gunicorn -w 4 -b 127.0.0.1:8001 main:app
```

### Error: "Alembic migration failed"

```bash
# Verificar que BD está disponible
mysql -h localhost -u TU_USUARIO -p TU_BD -e "SELECT 1;"

# Si funciona, ejecutar migraciones manualmente
alembic current
alembic upgrade head
```

---

## 📊 Verificaciones

```bash
# 1. Archivo extraído
ls -la /home/u938946830/jadslink-deploy/

# 2. .env configurado
grep DATABASE_URL /home/u938946830/jadslink-deploy/.env

# 3. Virtual env creado
ls -la /home/u938946830/jadslink-deploy/api/venv/

# 4. BD conectada
mysql -u u938946830_jadslink -p -e "SELECT 1;"

# 5. API corriendo
curl -s http://localhost:8000/health

# 6. PM2 status
pm2 status
```

---

## 📞 Próximos Pasos

1. ✅ Sistema en producción
2. Crear primer operador en Admin Panel
3. Configurar Stripe (opcional)
4. Monitorear logs: `pm2 logs jadslink-api`

---

## 📚 Documentación

- `RESUMEN_SETUP_HOSTINGER.md` - Resumen rápido
- `CLAUDE.md` - Arquitectura completa
- `api/requirements.txt` - Dependencias

---

**Status**: ✅ Sistema listo para Hostinger+MySQL
**Última actualización**: 2026-04-27
**Versión**: 2.0 (MySQL)
