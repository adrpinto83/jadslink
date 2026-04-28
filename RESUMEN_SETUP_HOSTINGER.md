# ⚡ Resumen Rápido: Setup JADSlink en Hostinger

**Fecha**: 2026-04-27
**Versión**: 1.0
**Tiempo estimado**: 30-45 minutos

---

## 📦 Archivos Generados

```
jadslink-deploy.tar.gz (508KB)  ← Subir a Hostinger
├── deploy-hostinger.sh         ← Script automatizado
├── .env.production             ← Template variables
├── INSTRUCCIONES_DESPLIEGUE.md ← Guía rápida
├── api/                        ← Backend FastAPI
├── dashboard/                  ← Frontend React
└── agent/                      ← Field nodes
```

---

## 🚀 Pasos Rápidos (5 minutos cada uno)

### 1. Subir Archivo (5 min)
```
Panel Hostinger → File Manager
/home/u938946830/ → Upload → jadslink-deploy.tar.gz
Click derecho → Extract
```

### 2. Crear Base de Datos (5 min)
```
Panel Hostinger → Bases de Datos → Crear Nueva
Nombre: jadslink
Usuario: jadslink_user
Contraseña: [generar fuerte]
Guardar credenciales
```

### 3. Configurar .env (5 min)
```bash
ssh -p 65002 u938946830@217.65.147.159
cd jadslink-deploy
nano .env

# Actualizar:
DATABASE_URL=postgresql://jadslink_user:TU_PASSWORD@localhost:5432/jadslink
SECRET_KEY=python3 -c "import secrets; print(secrets.token_hex(32))"
TICKET_HMAC_SECRET=python3 -c "import secrets; print(secrets.token_hex(32))"

# Guardar: Ctrl+O → Enter → Ctrl+X
```

### 4. Instalar & Setup (10 min)
```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Migraciones
alembic upgrade head

# Seed demo (opcional)
python3 scripts/reset_and_seed.py
```

### 5. Levantar API (5 min)
```bash
# Opción A: PM2
npm install -g pm2
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name jadslink-api

# Opción B: Systemd
sudo systemctl start jadslink-api
```

### 6. Configurar Nginx (5 min)
```
Panel Hostinger → Sitios Web → wheat-pigeon-347024.hostingersite.com
Configuración Avanzada → Nginx
[Copiar configuración de GUIA_HOSTINGER_COMPLETA.md]
Guardar
```

### 7. Compilar Dashboard (5 min)
```bash
cd dashboard
npm install
npm run build
```

### 8. Acceder (1 min)
```
https://wheat-pigeon-347024.hostingersite.com
Demo: demo@jadslink.com / demo123456
```

---

## 📋 Checklist

- [ ] Archivo TAR.GZ descargado
- [ ] Archivo subido y extraído en Hostinger
- [ ] Base de datos creada
- [ ] Archivo .env configurado
- [ ] Virtual environment creado
- [ ] Dependencias instaladas
- [ ] Migraciones ejecutadas
- [ ] Seed aplicado (opcional)
- [ ] API corriendo (PM2 o Systemd)
- [ ] Nginx configurado
- [ ] Dashboard compilado
- [ ] Acceso a https://wheat-pigeon-347024.hostingersite.com ✅

---

## 🆘 Si Algo Sale Mal

### "Cannot connect to database"
```bash
# Verificar credenciales de BD en .env
psql -h localhost -U jadslink_user -d jadslink
```

### "ModuleNotFoundError"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Port 8000 in use"
```bash
# Matar proceso
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# O cambiar puerto
gunicorn -w 4 -b 127.0.0.1:8001 main:app
```

### "403 Forbidden" en dashboard
```bash
cd dashboard
npm install
npm run build
chmod -R 755 /home/u938946830/jadslink-deploy
```

---

## 📚 Documentación Completa

- **GUIA_HOSTINGER_COMPLETA.md** - Paso a paso detallado
- **HOSTINGER_SETUP.md** - Configuración de BD
- **INSTRUCCIONES_DESPLIEGUE.md** - Dentro del TAR.GZ
- **CLAUDE.md** - Arquitectura del proyecto

---

## 🎯 Credenciales Demo

Después del seed:

```
OPERATOR:
Email: demo@jadslink.com
Password: demo123456

SUPERADMIN:
Email: admin@jads.com
Password: admin123456
```

---

## 📞 URLs Importantes

- **Panel Hostinger**: https://hostinger.com/account
- **Acceso SSH**:
  ```bash
  ssh -p 65002 u938946830@217.65.147.159
  ```
- **Dashboard**: https://wheat-pigeon-347024.hostingersite.com
- **API Docs**: https://wheat-pigeon-347024.hostingersite.com/api/docs

---

## ✅ Resultado Esperado

```
Status: ✅ Sistema en Producción

API:       https://wheat-pigeon-347024.hostingersite.com/api/health
Dashboard: https://wheat-pigeon-347024.hostingersite.com
Docs:      https://wheat-pigeon-347024.hostingersite.com/api/docs

Usuarios:  ✅ Funcionando
BD:        ✅ Funcionando
Sessions:  ✅ Funcionando
```

---

**Última actualización**: 2026-04-27
**Versión**: 1.0
**Status**: ✅ Listo para desplegar
