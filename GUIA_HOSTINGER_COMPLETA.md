# 🚀 Guía Completa: JADSlink en Hostinger

**Fecha**: 2026-04-27
**Dominio**: wheat-pigeon-347024.hostingersite.com
**Servidor**: 217.65.147.159:65002

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Paso 1: Subir Archivo de Deploy](#paso-1-subir-archivo-de-deploy)
3. [Paso 2: Crear Base de Datos](#paso-2-crear-base-de-datos)
4. [Paso 3: Configurar Variables de Entorno](#paso-3-configurar-variables-de-entorno)
5. [Paso 4: Instalar Dependencias](#paso-4-instalar-dependencias)
6. [Paso 5: Ejecutar Setup](#paso-5-ejecutar-setup)
7. [Paso 6: Levantar API](#paso-6-levantar-api)
8. [Paso 7: Configurar Nginx](#paso-7-configurar-nginx)
9. [Paso 8: Acceder al Sistema](#paso-8-acceder-al-sistema)
10. [Troubleshooting](#troubleshooting)

---

## ✅ Requisitos Previos

- **Acceso SSH** a Hostinger (credenciales proporcionadas)
- **Cliente SSH** en tu máquina (Terminal, PuTTY, etc.)
- **File Manager** o **SCP** para subir archivos
- **500MB** de espacio libre

---

## Paso 1: Subir Archivo de Deploy

### Opción A: File Manager de Hostinger (Recomendado)

1. **Login al Panel Hostinger**
   - URL: https://hostinger.com/account
   - Usuario: (tu email)

2. **Ir a → Administrador de archivos**
   - Navega a `/home/u938946830/`

3. **Subir archivo**
   - Click "Upload"
   - Selecciona: `jadslink-deploy.tar.gz`
   - Espera a que termine (508KB)

4. **Extraer archivo**
   - Click derecho sobre `jadslink-deploy.tar.gz`
   - Select "Extract"
   - Carpeta destino: `/home/u938946830/`

### Opción B: SSH/SCP (Terminal)

```bash
# Desde tu máquina local
scp -P 65002 jadslink-deploy.tar.gz u938946830@217.65.147.159:/home/u938946830/

# Luego conectar y extraer
ssh -p 65002 u938946830@217.65.147.159
tar -xzf jadslink-deploy.tar.gz
```

### Opción C: Git (si quieres mantener sincronizado)

```bash
ssh -p 65002 u938946830@217.65.147.159
cd /home/u938946830/
git clone https://github.com/adrpinto83/jadslink.git
```

---

## Paso 2: Crear Base de Datos

### En Panel Hostinger

1. **Ir a → Bases de Datos**
2. **Click "Crear Nueva Base de Datos"**
3. **Llenar formulario:**

   | Campo | Valor |
   |-------|-------|
   | **Nombre BD** | `jadslink` |
   | **Usuario** | `jadslink_user` |
   | **Contraseña** | (generar fuerte - mín 12 caracteres) |
   | **Host** | `localhost` o IP que muestre Hostinger |
   | **Puerto** | `5432` |

4. **Guardar credenciales** en un archivo seguro

**Respuesta esperada de Hostinger:**
```
✅ Base de datos creada
Hostname: localhost
Usuario: jadslink_user
Contraseña: xxxxxxxxxxxxx
Base de datos: jadslink
Puerto: 5432
```

---

## Paso 3: Configurar Variables de Entorno

### Conectar por SSH

```bash
ssh -p 65002 u938946830@217.65.147.159
cd /home/u938946830/jadslink-deploy
```

### Copiar Template

```bash
cp .env.production .env
```

### Editar .env

```bash
nano .env
```

### Actualizar Líneas Importantes

```bash
# ===== URLS =====
API_BASE_URL=https://wheat-pigeon-347024.hostingersite.com/api
FRONTEND_URL=https://wheat-pigeon-347024.hostingersite.com

# ===== BASE DE DATOS (ACTUALIZAR CON TUS CREDENCIALES) =====
DATABASE_URL=postgresql://jadslink_user:TU_CONTRASEÑA@localhost:5432/jadslink

# ===== GENERAR NUEVAS CLAVES SEGURAS =====
# Ejecutar en terminal:
# python3 -c "import secrets; print(secrets.token_hex(32))"

SECRET_KEY=PEGA_AQUI_LA_CLAVE_GENERADA
TICKET_HMAC_SECRET=PEGA_AQUI_LA_SEGUNDA_CLAVE
```

### Guardar el Archivo

1. Presiona: `Ctrl + O`
2. Presiona: `Enter`
3. Presiona: `Ctrl + X`

✅ Archivo guardado

---

## Paso 4: Instalar Dependencias

### Verificar Python

```bash
python3 --version
# Debe ser 3.9+
```

### Crear Virtual Environment

```bash
cd /home/u938946830/jadslink-deploy/api
python3 -m venv venv
source venv/bin/activate
```

**Output esperado:**
```
(venv) u938946830@server:~/jadslink-deploy/api$
```

### Instalar Requirements

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Output esperado:**
```
Successfully installed 45 packages
```

### Verificar Instalación

```bash
python3 -c "import fastapi; print('✅ FastAPI OK')"
```

---

## Paso 5: Ejecutar Setup

### Desde la carpeta API con venv activado

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
✅ Nuevas tablas creadas
```

### Aplicar Seed de Datos (Opcional)

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

## Paso 6: Levantar API

### Opción A: PM2 (Recomendado para Producción)

```bash
# Instalar PM2 globalmente
npm install -g pm2

# Desde /home/u938946830/jadslink-deploy/api
cd /home/u938946830/jadslink-deploy/api
source venv/bin/activate

# Iniciar API
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name jadslink-api

# Hacer que se reinicie automáticamente
pm2 save
pm2 startup
```

### Verificar Estado

```bash
pm2 status
pm2 logs jadslink-api
```

### Opción B: Systemd Service (Alternativa)

```bash
# Crear archivo service
sudo nano /etc/systemd/system/jadslink-api.service
```

**Contenido:**
```ini
[Unit]
Description=JADSlink API
After=network.target

[Service]
Type=notify
User=u938946830
WorkingDirectory=/home/u938946830/jadslink-deploy/api
Environment="PATH=/home/u938946830/jadslink-deploy/api/venv/bin"
ExecStart=/home/u938946830/jadslink-deploy/api/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Activar:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable jadslink-api
sudo systemctl start jadslink-api
sudo systemctl status jadslink-api
```

---

## Paso 7: Configurar Nginx

### En Panel Hostinger

1. **Ir a → Sitios Web** (o Domains)
2. **Click en** `wheat-pigeon-347024.hostingersite.com`
3. **Ir a → Configuración Avanzada → Nginx**
4. **Reemplazar configuración actual con:**

```nginx
# Proxy a la API
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}

# Servir dashboard React
location / {
    alias /home/u938946830/jadslink-deploy/dashboard/dist/;
    try_files $uri $uri/ /index.html;
    expires 1h;
}

# Assets estáticos (cache long)
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    alias /home/u938946830/jadslink-deploy/dashboard/dist/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

5. **Click "Guardar"**

---

## Paso 8: Acceder al Sistema

### Health Check (Terminal)

```bash
curl -v http://localhost:8000/health

# Respuesta esperada:
# {"status":"healthy","checks":{"database":"ok"}}
```

### Desde Navegador

```
https://wheat-pigeon-347024.hostingersite.com
```

### Login Demo

- **Email**: `demo@jadslink.com`
- **Contraseña**: `demo123456`

### Login Admin (Superadmin)

- **Email**: `admin@jads.com`
- **Contraseña**: `admin123456`

---

## 🐛 Troubleshooting

### Error: "Cannot connect to database"

```bash
# Verificar credenciales
psql -h localhost -U jadslink_user -d jadslink

# Si error, verificar en Hostinger:
# 1. Base de datos existe: jadslink
# 2. Usuario existe: jadslink_user
# 3. Contraseña es correcta
# 4. Host es correcto (localhost o IP)
```

### Error: "ModuleNotFoundError"

```bash
# Reinstalar dependencias
cd api
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Port 8000 already in use"

```bash
# Cambiar puerto en gunicorn
gunicorn -w 4 -b 127.0.0.1:8001 main:app

# O matar proceso actual:
lsof -i :8000
kill -9 <PID>
```

### Error: "CORS error"

El error es normal. El frontend debe estar servido por Nginx desde el mismo dominio.

```bash
# Verificar en consola del navegador:
# GET https://wheat-pigeon-347024.hostingersite.com ✅
# GET https://wheat-pigeon-347024.hostingersite.com/api/health ✅
```

### Error: "403 Forbidden"

```bash
# Verificar permisos de carpetas
chmod -R 755 /home/u938946830/jadslink-deploy/

# Dashboard build no existe
cd /home/u938946830/jadslink-deploy/dashboard
npm install
npm run build
```

### Error: "Alembic migration failed"

```bash
# Verificar que BD está disponible
psql -h localhost -U jadslink_user -d jadslink

# Ejecutar migraciones manualmente
cd api
source venv/bin/activate
alembic current
alembic history
alembic upgrade head
```

---

## 🔍 Verificaciones

### Checklist Completo

```bash
# 1. Archivo extraído
[ ] ls /home/u938946830/jadslink-deploy/

# 2. .env configurado
[ ] grep DATABASE_URL /home/u938946830/jadslink-deploy/.env

# 3. Virtual env creado
[ ] ls /home/u938946830/jadslink-deploy/api/venv/

# 4. Dependencias instaladas
[ ] /home/u938946830/jadslink-deploy/api/venv/bin/pip list | wc -l

# 5. BD disponible
[ ] psql -h localhost -U jadslink_user -d jadslink -c "SELECT 1"

# 6. Migraciones ejecutadas
[ ] curl http://localhost:8000/health

# 7. API corriendo
[ ] pm2 status

# 8. Nginx configurado
[ ] curl https://wheat-pigeon-347024.hostingersite.com

# 9. Login funciona
[ ] Acceder a dashboard en navegador
```

---

## 📞 Próximos Pasos

### 1. Compilar Dashboard

```bash
cd /home/u938946830/jadslink-deploy/dashboard
npm install
npm run build
```

### 2. Restartear Nginx (si es necesario)

```bash
# En panel Hostinger: Administrador de sitios web → Restart
# O por terminal:
sudo systemctl restart nginx
```

### 3. Verificar en Navegador

```
https://wheat-pigeon-347024.hostingersite.com
```

### 4. Crear Primer Operador

- Login como admin@jads.com
- Ir a Admin Panel
- Crear nuevo operador

### 5. Activar Stripe (Opcional)

- Crear cuenta en Stripe
- Configurar claves en .env
- Actualizar planes de suscripción

---

## 📚 Documentación Adicional

- **HOSTINGER_SETUP.md** - Guía corta
- **CLAUDE.md** - Arquitectura completa
- **api/requirements.txt** - Dependencias Python
- **dashboard/package.json** - Dependencias Node.js

---

## 🆘 Contacto y Soporte

- **Email**: adrpinto83@gmail.com
- **GitHub**: https://github.com/adrpinto83/jadslink
- **Issues**: https://github.com/adrpinto83/jadslink/issues

---

**Status**: ✅ Listo para desplegar
**Última actualización**: 2026-04-27
**Versión**: 1.0
