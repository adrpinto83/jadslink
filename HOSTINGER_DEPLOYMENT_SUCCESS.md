# 🚀 JADSlink - DESPLIEGUE EXITOSO EN HOSTINGER

## ✅ Estado: SISTEMA COMPLETAMENTE OPERATIVO

---

## 📍 Acceso Público

**URL Principal:**
```
https://wheat-pigeon-347024.hostingersite.com
```

**Endpoints de API:**
```
https://wheat-pigeon-347024.hostingersite.com/api/v1/...
```

**Documentación:**
```
https://wheat-pigeon-347024.hostingersite.com/docs (Swagger UI)
https://wheat-pigeon-347024.hostingersite.com/redoc (ReDoc)
```

---

## 🔐 Credenciales de Acceso

| Campo | Valor |
|-------|-------|
| **Email** | admin@jads.com |
| **Contraseña** | admin123456 |
| **Rol** | Superadmin |

---

## 🏗️ Arquitectura del Despliegue

```
Usuario Final
    ↓
HTTPS (Certificado Let's Encrypt)
    ↓
LiteSpeed Web Server (Hostinger)
    ↓
/public_html/
├── index.html (Página de bienvenida)
├── api.php (Proxy PHP → API)
└── .htaccess (Rewrite rules)
    ↓
Uvicorn (127.0.0.1:8000)
    ↓
FastAPI Application
    ↓
MySQL Database (127.0.0.1:3306)
```

---

## 📋 Componentes Desplegados

### 1. **Página de Inicio**
- **Archivo**: `/public_html/index.html`
- **Estado**: ✅ Operativa
- **Características**:
  - Página de bienvenida con estilo moderno
  - Verificación automática del estado de la API
  - Enlaces a documentación
  - Botón de login de prueba

### 2. **API Proxy PHP**
- **Archivo**: `/public_html/api.php`
- **Estado**: ✅ Funcional
- **Función**: Redirecciona todas las requests a Uvicorn

### 3. **Rewrite Rules (Apache)**
- **Archivo**: `/public_html/.htaccess`
- **Estado**: ✅ Configurado
- **Reglas**:
  - `/` → `index.html`
  - `/api/v1/*` → `api.php` → Uvicorn
  - `/health` → `api.php` → Uvicorn
  - `/docs` → `api.php` → Uvicorn
  - `/redoc` → `api.php` → Uvicorn

### 4. **Backend API (Uvicorn)**
- **Directorio**: `/home/u938946830/jadslink-deploy/api/`
- **Puerto**: 8000 (interno)
- **Estado**: ✅ Corriendo
- **Comando**: `python3 -m uvicorn main:app --host 127.0.0.1 --port 8000`

### 5. **Base de Datos (MySQL)**
- **Host**: 127.0.0.1:3306
- **Usuario**: u938946830_jadslink
- **Base de datos**: u938946830_jadslink
- **Estado**: ✅ Conectada y operativa
- **Tablas**: 10 (tenants, users, nodes, plans, tickets, sessions, etc.)

---

## 🔗 Rutas Disponibles

### Autenticación
```
POST   /api/v1/auth/login          - Iniciar sesión
POST   /api/v1/auth/refresh        - Renovar token
GET    /api/v1/auth/me             - Datos del usuario actual
```

### Tenants
```
GET    /api/v1/tenants/me          - Información del tenant actual
PATCH  /api/v1/tenants/me          - Actualizar configuración
```

### Planes
```
GET    /api/v1/plans/              - Listar planes
POST   /api/v1/plans/              - Crear plan
GET    /api/v1/plans/{id}          - Detalle del plan
PATCH  /api/v1/plans/{id}          - Actualizar plan
DELETE /api/v1/plans/{id}          - Eliminar plan
```

### Nodos
```
GET    /api/v1/nodes/              - Listar nodos
POST   /api/v1/nodes/              - Crear nodo
GET    /api/v1/nodes/{id}          - Detalle del nodo
PATCH  /api/v1/nodes/{id}          - Actualizar nodo
```

### Tickets
```
GET    /api/v1/tickets/            - Listar tickets
POST   /api/v1/tickets/generate    - Generar tickets
GET    /api/v1/tickets/{code}      - Detalle del ticket
```

Y muchos más... Consultar `/docs` para lista completa.

---

## 🧪 Pruebas Rápidas

### 1. Health Check
```bash
curl https://wheat-pigeon-347024.hostingersite.com/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok"
  },
  "timestamp": "2026-04-28T00:53:10.170466+00:00"
}
```

### 2. Login
```bash
curl -X POST https://wheat-pigeon-347024.hostingersite.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@jads.com","password":"admin123456"}'
```

**Respuesta esperada:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### 3. Usar Token
```bash
curl https://wheat-pigeon-347024.hostingersite.com/api/v1/auth/me \
  -H 'Authorization: Bearer <token>'
```

---

## 🔧 Administración del Sistema

### Ver estado de Uvicorn
```bash
ssh -p 65002 u938946830@217.65.147.159
ps aux | grep 'python3 -m uvicorn'
```

### Reiniciar API
```bash
ssh -p 65002 u938946830@217.65.147.159 \
  'pkill -f "python3 -m uvicorn" && \
   sleep 2 && \
   cd /home/u938946830/jadslink-deploy/api && \
   nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 &'
```

### Ver logs
```bash
ssh -p 65002 u938946830@217.65.147.159 'tail -f /tmp/uvicorn.log'
```

### Conexión MySQL
```bash
ssh -p 65002 u938946830@217.65.147.159 \
  'mysql -h 127.0.0.1 -u u938946830_jadslink -p"xNFWgR1w>" u938946830_jadslink'
```

---

## 📊 Información de Instalación

| Aspecto | Detalles |
|--------|----------|
| **Servidor** | Hostinger Cloud Startup Hosting |
| **IP** | 217.65.147.159 |
| **Puerto SSH** | 65002 |
| **Usuario SSH** | u938946830 |
| **Dominio** | wheat-pigeon-347024.hostingersite.com |
| **SSL** | Let's Encrypt (automático) |
| **Python** | 3.9 |
| **PHP** | 8.3.30 |
| **Web Server** | LiteSpeed |

---

## 🛠️ Tecnologías Utilizadas

**Backend:**
- FastAPI 0.115+
- Uvicorn (ASGI Server)
- SQLAlchemy 2.0+ (ORM async)
- Alembic (Migraciones)
- MySQL + aiomysql (Driver async)
- JWT (Autenticación)
- Pydantic 2.0+ (Validación)

**Frontend (disponible):**
- React 18
- TypeScript 5
- Vite 6
- TailwindCSS 3
- TanStack Router

**Proxy:**
- PHP 8.3 (cURL)
- Apache Rewrite Module
- .htaccess

---

## 📝 Notas Importantes

1. **Contraseña con carácter especial**: La contraseña MySQL contiene `>`, por lo que siempre usar `127.0.0.1` en lugar de `localhost` (IPv4 vs IPv6)

2. **Proxy PHP**: Implementado porque Hostinger Shared Hosting no soporta mod_proxy de Apache

3. **Redis no disponible**: El sistema funciona correctamente sin Redis (cache deshabilitado)

4. **Email no configurado**: No hay servidor SMTP configurado, pero se puede agregar Resend/SendGrid más adelante

5. **Soft deletes**: Implementados en la base de datos (columna `deleted_at`)

---

## 🚀 Próximos Pasos (Opcionales)

### 1. Cambiar Credenciales
```bash
ssh -p 65002 u938946830@217.65.147.159
cd /home/u938946830/jadslink-deploy/api
python3 -c "
from services.auth_service import hash_password
print(hash_password('tu-nueva-contraseña'))
"
# Luego actualizar en base de datos
```

### 2. Configurar Email (SendGrid/Resend)
Editar `.env`:
```
RESEND_API_KEY=re_xxxxx
```

### 3. Compilar Dashboard React
```bash
cd /home/u938946830/jadslink-deploy/dashboard
npm run build
# Copiar dist/ a /home/u938946830/domains/wheat-pigeon-347024.hostingersite.com/public_html/dashboard
```

### 4. Usar Dominio Personalizado
- Registrar dominio
- Cambiar nameservers en Hostinger
- Actualizar ALLOWED_ORIGINS en .env

---

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| API retorna 500 | Ver logs: `tail -f /tmp/uvicorn.log` |
| Login no funciona | Verificar credenciales en base de datos |
| Proxy error 500 | Verificar que Uvicorn está corriendo |
| CORS error | Actualizar ALLOWED_ORIGINS en .env |
| Base de datos offline | Verificar conexión SSH a Hostinger |

---

## 📞 Contacto & Soporte

**Proyecto**: JADSlink v1.0 - MySQL Edition
**Ambiente**: Hostinger Cloud Startup
**Fecha de Deploy**: 2026-04-28
**Estado**: ✅ Producción

Para soporte técnico, contactar al equipo de JADS Studio.

---

**El sistema está listo para usar. ¡Accede a https://wheat-pigeon-347024.hostingersite.com!** 🎉
