# Setup JADSlink en Hostinger - Guía de Configuración

**Fecha**: 2026-04-27
**Estado**: Proyecto deployado en Hostinger, pendiente configuración de BD

---

## 📋 Checklist de Setup en Hostinger

### ✅ Completado
- [x] ZIP descargado y extraído en Hostinger
- [x] Archivo `.env.example` presente

### 🔲 Pendiente
- [ ] Base de datos PostgreSQL creada
- [ ] `.env` configurado con credenciales de BD
- [ ] Migraciones Alembic ejecutadas
- [ ] Seed de datos ejecutado
- [ ] API levantada (PM2 o systemd)

---

## 1️⃣ Crear Base de Datos en Hostinger

En el **Panel de Control** → **Bases de Datos**:

```
1. Click "Crear Nueva Base de Datos"
2. Nombre: jadslink
3. Usuario: jadslink_user
4. Contraseña: [genera fuerte]
5. Click Crear

Anotá los datos que te muestra Hostinger:
- Host: localhost (o IP interna)
- Puerto: 5432
- Usuario: jadslink_user
- Contraseña: [la que generaste]
- BD: jadslink
```

---

## 2️⃣ Configurar .env

SSH a tu servidor:

```bash
ssh usuario@dominio.com
cd /home/usuario/jadslink-deploy

# Copiar template
cp .env.example .env

# Editar
nano .env
```

**Actualiza estas variables:**

```bash
# ===== BASE DE DATOS =====
DATABASE_URL=postgresql://jadslink_user:TU_CONTRASEÑA@localhost:5432/jadslink
REDIS_URL=redis://localhost:6379/0

# ===== SEGURIDAD =====
# Genera nuevo SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
# Cópialo al .env

# ===== DOMINIO =====
FRONTEND_URL=https://tu-dominio-temporal.hostingersite.com
BACKEND_URL=https://tu-dominio-temporal.hostingersite.com/api

# ===== EMAIL (OPCIONAL POR AHORA) =====
RESEND_API_KEY=re_xxx
EMAIL_FROM=noreply@tu-dominio.com
```

Guarda con: `Ctrl+O` → `Enter` → `Ctrl+X`

---

## 3️⃣ Instalar Dependencias

```bash
cd /home/usuario/jadslink-deploy/api

# Crear virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Instalar requirements
pip install -r requirements.txt
```

---

## 4️⃣ Ejecutar Migraciones

```bash
# Desde /home/usuario/jadslink-deploy/api (con venv activado)

alembic upgrade head
```

**Output esperado:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> e8207eb00a46, add_deleted_at_to_pricing_configs
INFO  [alembic.migration] Running upgrade e8207eb00a46 -> eb6f7ed4e560, add_wan_ip_column_to_nodes
[... más migraciones ...]
```

---

## 5️⃣ Seed de Datos Demo

```bash
# Desde /home/usuario/jadslink-deploy/api (con venv activado)

python scripts/reset_and_seed.py
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

## 6️⃣ Levantar API

**Opción A: PM2 (Recomendado)**

```bash
# Instalar PM2 globalmente
npm install -g pm2

# En /home/usuario/jadslink-deploy/api
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name "jadslink-api"

# Verificar
pm2 status
pm2 logs jadslink-api
```

**Opción B: Systemd Service**

Crear `/etc/systemd/system/jadslink-api.service`:

```ini
[Unit]
Description=JADSlink API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/usuario/jadslink-deploy/api
Environment="PATH=/home/usuario/jadslink-deploy/api/venv/bin"
ExecStart=/home/usuario/jadslink-deploy/api/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jadslink-api
sudo systemctl start jadslink-api
sudo systemctl status jadslink-api
```

---

## 7️⃣ Verificar que Funciona

```bash
# Health check
curl http://localhost:8000/health

# Debe responder:
# {"status":"healthy","checks":{"database":"ok"}}
```

---

## 🔧 Troubleshooting

### Error: Cannot connect to database
```bash
# Verificar credenciales
psql postgresql://usuario:pass@localhost:5432/jadslink
```

### Error: Redis connection failed
```bash
# Verificar Redis
redis-cli ping
# Debe responder: PONG
```

### Error: ModuleNotFoundError
```bash
# Reinstalar con venv activado
source venv/bin/activate
pip install -r requirements.txt
```

### Error: Port already in use
```bash
# Cambiar puerto en gunicorn
gunicorn -w 4 -b 127.0.0.1:8001 main:app
```

---

## 📞 Próximos Pasos

Una vez que el API esté corriendo:

1. **Configurar Frontend**
   ```bash
   cd /home/usuario/jadslink-deploy/dashboard
   npm install
   npm run build
   # Copiar dist/ a carpeta pública
   ```

2. **Configurar Nginx** (para proxy reverso)
   ```nginx
   location /api {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host $host;
   }
   ```

3. **SSL con Let's Encrypt**
   ```bash
   sudo certbot --nginx -d tu-dominio.com
   ```

4. **Verificar desde navegador**
   ```
   https://tu-dominio.com/login
   Demo: demo@jadslink.com / demo123456
   ```

---

## 📚 Referencias

- `QUICK_START.md` - Setup rápido
- `DEPLOYMENT.md` - Guía completa paso a paso
- `INSTRUCCIONES_HOSTINGER.md` - Hostinger específico
- `.env.example` - Todas las variables disponibles
- `api/requirements.txt` - Dependencias Python

---

**Status**: Listo para configurar BD en Hostinger
**Próxima sesión**: Finalizar setup de BD y levantar API
