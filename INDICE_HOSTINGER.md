# 📚 Índice: JADSlink en Hostinger

**Última actualización**: 2026-04-27
**Versión**: 2.0 (MySQL)
**Status**: ✅ Listo para desplegar

---

## 🎯 Comienza Aquí

### Si no sabes por dónde empezar:
**Lee en este orden:**

1. **[HOSTINGER_CREDENCIALES_BD.md](./HOSTINGER_CREDENCIALES_BD.md)** (5 minutos)
   - Cómo obtener credenciales de base de datos en Hostinger
   - Cómo construir el DATABASE_URL
   - Verificación rápida

2. **[HOSTINGER_MYSQL_SETUP.md](./HOSTINGER_MYSQL_SETUP.md)** (30 minutos)
   - Guía completa paso a paso
   - Todas las instrucciones detalladas
   - Troubleshooting exhaustivo

3. **[DESPLIEGUE_HOSTINGER_FINAL.md](./DESPLIEGUE_HOSTINGER_FINAL.md)** (10 minutos)
   - Resumen rápido de todo
   - Checklist de instalación
   - Verificaciones finales

---

## 📦 Archivo de Despliegue

```
jadslink-deploy-mysql.tar.gz (505 KB)
│
├── api/                          Backend FastAPI
│   ├── requirements.txt           ✅ Actualizado (aiomysql)
│   ├── config.py                  ✅ Actualizado (MySQL)
│   ├── database.py                ✅ Actualizado (Pool MySQL)
│   ├── .env.hostinger             ✅ NUEVO (Template)
│   ├── main.py
│   ├── models/                    100% compatible
│   ├── routers/                   100% compatible
│   ├── migrations/                100% compatible
│   ├── scripts/
│   │   └── reset_and_seed.py     Para datos demo
│   └── [otros archivos]
│
├── dashboard/                     Frontend React
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── [otros archivos]
│
├── agent/                         Field nodes (opcional)
│   └── [archivos agent]
│
├── HOSTINGER_MYSQL_SETUP.md      ⭐ GUÍA PRINCIPAL
├── DESPLIEGUE_HOSTINGER_FINAL.md ⭐ RESUMEN Y CHECKLIST
├── CAMBIOS_POSTGRESQL_A_MYSQL.md ⭐ DETALLES TÉCNICOS
├── deploy-hostinger.sh           Script de deploy
└── [otros archivos]
```

---

## 📖 Documentación por Caso de Uso

### 🎯 "Quiero empezar ya"
Lee:
1. [HOSTINGER_CREDENCIALES_BD.md](./HOSTINGER_CREDENCIALES_BD.md) (5 min)
2. [DESPLIEGUE_HOSTINGER_FINAL.md](./DESPLIEGUE_HOSTINGER_FINAL.md) (10 min)
3. Ejecuta los 6 pasos rápidos

### 🛠️ "Quiero instrucciones detalladas"
Lee:
1. [HOSTINGER_CREDENCIALES_BD.md](./HOSTINGER_CREDENCIALES_BD.md)
2. [HOSTINGER_MYSQL_SETUP.md](./HOSTINGER_MYSQL_SETUP.md) (GUÍA COMPLETA)
3. Sigue todos los pasos

### 🔧 "Quiero entender qué cambió"
Lee:
1. [CAMBIOS_POSTGRESQL_A_MYSQL.md](./CAMBIOS_POSTGRESQL_A_MYSQL.md)
2. Secciones técnicas en [HOSTINGER_MYSQL_SETUP.md](./HOSTINGER_MYSQL_SETUP.md)

### 🐛 "Tengo problemas"
Lee:
1. [HOSTINGER_MYSQL_SETUP.md](./HOSTINGER_MYSQL_SETUP.md) → Sección "Troubleshooting"
2. [HOSTINGER_CREDENCIALES_BD.md](./HOSTINGER_CREDENCIALES_BD.md) → Sección "Problemas Comunes"

### 📋 "Quiero ver todo el checklist"
Lee:
1. [DESPLIEGUE_HOSTINGER_FINAL.md](./DESPLIEGUE_HOSTINGER_FINAL.md) → Sección "Checklist"

---

## 📚 Documentación Completa

| Archivo | Propósito | Público | Cuándo Leer |
|---------|-----------|---------|-----------|
| **HOSTINGER_CREDENCIALES_BD.md** | Obtener datos de BD en Hostinger | ⭐⭐⭐ Esencial | Primero |
| **HOSTINGER_MYSQL_SETUP.md** | Guía paso a paso (10 pasos) | ⭐⭐⭐ Completa | Principal |
| **DESPLIEGUE_HOSTINGER_FINAL.md** | Resumen y checklist | ⭐⭐ Rápida | Referencia |
| **CAMBIOS_POSTGRESQL_A_MYSQL.md** | Cambios técnicos realizados | ⭐ Técnica | Opcional |
| **INDICE_HOSTINGER.md** | Este archivo | ⭐⭐ Navegación | Ahora mismo |

---

## 🚀 Pasos Rápidos de Instalación

Si ya tienes todo listo, aquí están los 6 pasos:

### 1️⃣ Subir a Hostinger
```bash
Panel Hostinger → File Manager → /home/u938946830/
Upload: jadslink-deploy-mysql.tar.gz
Derecho: Extract
```

### 2️⃣ Obtener credenciales de BD
```
Panel Hostinger → Bases de Datos
Copiar: Host, Usuario, Contraseña, Puerto, BD
```

### 3️⃣ Configurar .env
```bash
cd jadslink-deploy
cp api/.env.hostinger .env
nano .env
# Actualizar: DATABASE_URL=mysql+aiomysql://USER:PASS@localhost:3306/DB
```

### 4️⃣ Instalar
```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### 5️⃣ Ejecutar
```bash
npm install -g pm2
pm2 start "gunicorn -w 4 -b 127.0.0.1:8000 main:app" --name jadslink-api
```

### 6️⃣ Acceder
```
https://wheat-pigeon-347024.hostingersite.com
Demo: demo@jadslink.com / demo123456
```

---

## ✅ Cambios Realizados

### Código Modificado
- ✅ `api/requirements.txt` - asyncpg → aiomysql
- ✅ `api/config.py` - DATABASE_URL MySQL
- ✅ `api/database.py` - Pool y charset MySQL
- ✅ `deploy-hostinger.sh` - Script actualizado

### Archivos Nuevos
- ✅ `api/.env.hostinger` - Template para Hostinger
- ✅ `HOSTINGER_MYSQL_SETUP.md` - Guía MySQL
- ✅ `DESPLIEGUE_HOSTINGER_FINAL.md` - Checklist
- ✅ `CAMBIOS_POSTGRESQL_A_MYSQL.md` - Detalles técnicos
- ✅ `HOSTINGER_CREDENCIALES_BD.md` - BD helper
- ✅ `INDICE_HOSTINGER.md` - Este archivo

### Sin Cambios
- ✅ Frontend React (100% compatible)
- ✅ Modelos SQLAlchemy (100% compatible)
- ✅ Migraciones Alembic (100% compatible)
- ✅ API endpoints (100% compatible)

---

## 🔐 Información de Configuración

### DATABASE_URL Format
```
mysql+aiomysql://[usuario]:[contraseña]@[host]:[puerto]/[basedatos]
```

### Ejemplo Real
```
mysql+aiomysql://u938946830_jadslink:MyPassword123@localhost:3306/u938946830_jadslink
```

### Obtener en Hostinger
Panel → Bases de Datos → Seleccionar BD → Ver detalles

---

## 📊 Compatibilidad

| BD | Versión | Status |
|----|---------|--------|
| MySQL | 5.7+ | ✅ Compatible |
| MariaDB | 10.3+ | ✅ Compatible |
| SQLite | Cualquiera | ✅ Compatible (dev) |
| PostgreSQL | Cualquiera | ⚠️ Requiere rollback |

---

## 🎯 Flujo de Instalación Visual

```
Descarga
   ↓
Sube a Hostinger
   ↓
Extrae archivo
   ↓
Obtén credenciales de BD
   ↓
Copia .env.hostinger → .env
   ↓
Edita DATABASE_URL
   ↓
Crea virtual env
   ↓
Instala dependencias
   ↓
Ejecuta migraciones
   ↓
Ejecuta API con PM2
   ↓
¡Accede a tu sistema!
```

---

## 📞 Preguntas Frecuentes

### ¿Dónde obtengo el archivo?
**Respuesta**: `jadslink-deploy-mysql.tar.gz` está en `/home/adrpinto/jadslink/`

### ¿Qué versión de Python necesito?
**Respuesta**: Python 3.9+ (Hostinger proporciona 3.9.21)

### ¿Necesito PostgreSQL?
**Respuesta**: No, este es para MySQL/MariaDB

### ¿Puedo volver a PostgreSQL?
**Respuesta**: Sí, leyendo [CAMBIOS_POSTGRESQL_A_MYSQL.md](./CAMBIOS_POSTGRESQL_A_MYSQL.md) sección "Rollback"

### ¿Dónde pongo el .env?
**Respuesta**: En `/home/u938946830/jadslink-deploy/` (raíz del proyecto)

### ¿Y si tengo problemas con MySQL?
**Respuesta**: Lee [HOSTINGER_MYSQL_SETUP.md](./HOSTINGER_MYSQL_SETUP.md) sección "Troubleshooting"

---

## 🔍 Verificaciones Finales

Después de instalar, verifica que todo funciona:

```bash
# 1. BD conecta
mysql -h localhost -u TU_USUARIO -p

# 2. API está corriendo
pm2 status

# 3. API responde
curl -s http://localhost:8000/health

# 4. Acceder en navegador
https://wheat-pigeon-347024.hostingersite.com
```

---

## 📍 Estructura del Proyecto

```
/home/u938946830/jadslink-deploy/
├── api/                           Código backend
│   ├── main.py                   Punto de entrada FastAPI
│   ├── config.py                 Configuración (con MySQL default)
│   ├── database.py               Conexión (optimizado MySQL)
│   ├── requirements.txt           Dependencias (con aiomysql)
│   ├── .env.hostinger            Template de config
│   ├── models/                   Modelos SQLAlchemy
│   ├── routers/                  Rutas de API
│   ├── migrations/               Alembic migrations
│   ├── scripts/                  Scripts helper
│   └── venv/                     Virtual env (después de instalar)
│
├── dashboard/                     Código frontend
│   ├── src/                      Código fuente React
│   ├── package.json              Dependencias npm
│   ├── dist/                     Build compilado (después de build)
│   └── [otros archivos]
│
├── agent/                         Field nodes (opcional)
│   └── [archivos agent]
│
├── .env                          Tu configuración (CREAR)
├── HOSTINGER_MYSQL_SETUP.md      Guía principal
└── [otros archivos]
```

---

## 🎓 Recursos de Aprendizaje

### Documentación Oficial
- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Alembic: https://alembic.sqlalchemy.org

### Comandos Útiles
```bash
# Ver estado de API
pm2 status
pm2 logs jadslink-api

# Conectar a BD
mysql -h localhost -u usuario -p basedatos

# Ver variables de entorno
cat .env | grep DATABASE_URL
```

---

## ✨ Consideraciones Finales

### Seguridad
- [x] .env no se commita a Git
- [x] Contraseñas fuertes en BD
- [x] HTTPS obligatorio en producción
- [x] Secretos guardados en .env

### Performance
- [x] MySQL pooling configurado
- [x] Connection recycling cada 1 hora
- [x] Pool pre-ping habilitado
- [x] Charset optimizado (utf8mb4)

### Mantenibilidad
- [x] Código limpio y comentado
- [x] Documentación completa
- [x] Scripts de setup automatizados
- [x] Migración sin problemas

---

**¡Ahora estás listo para desplegar JADSlink en Hostinger! 🚀**

---

**Documento**: Índice de JADSlink en Hostinger
**Versión**: 2.0 (MySQL)
**Última actualización**: 2026-04-27
**Status**: ✅ Listo
