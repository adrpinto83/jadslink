# JADSlink - Despliegue en Hostinger COMPLETADO

## Status: ✅ SISTEMA FUNCIONAL

### Lo que se ha completado:

#### 1. Correcciones de Compatibilidad
- ✅ Python 3.9: Convertida sintaxis `type | None` a `Optional[type]` en 16 archivos
- ✅ PostgreSQL → MySQL: Adaptados todos los modelos y drivers
- ✅ Alembic migrations: Corregidas para funcionar en MySQL

#### 2. Base de Datos
- ✅ MySQL conectado (127.0.0.1:3306)
- ✅ 10 tablas creadas correctamente
- ✅ Índices y relaciones establecidas
- ✅ Seed data creado

#### 3. API FastAPI
- ✅ Uvicorn corriendo en puerto 8000
- ✅ `/health` endpoint respondiendo
- ✅ Login funcional
- ✅ JWT authentication funcionando

#### 4. Credenciales de Acceso
- **Superadmin**: admin@jads.com / admin123456
- **Operator Demo**: operator@test.com / operator123456

### Información de Conectividad

```
SSH: ssh -p 65002 u938946830@217.65.147.159
Directorio API: /home/u938946830/jadslink-deploy/api
Puerto Uvicorn: 127.0.0.1:8000
Base de Datos: mysql+aiomysql://u938946830_jadslink:xNFWgR1w>@127.0.0.1:3306/u938946830_jadslink
```

### Próximos Pasos Requeridos

#### CRÍTICO: Configurar Nginx Reverse Proxy
En el panel de Hostinger:
1. Ir a Sitios Web → wheat-pigeon-347024.hostingersite.com
2. Configurar que apunte a 127.0.0.1:8000
3. Sin esto, el dominio no podrá acceder a la API

#### Optional: React Dashboard
```bash
cd /home/u938946830/jadslink-deploy/dashboard
npm run build
# Copiar dist/ a public_html/dashboard
```

### Archivos Modificados para MySQL

**Migraciones corregidas:**
- `e60378fd8260_add_deleted_at_field_for_soft_deletes.py` - Comentados DROP de índices MySQL
- `f9c8e5d4c3b2_fix_plantier_enum_values.py` - PostgreSQL enum → no-op MySQL
- `e160bea57250_add_full_name_and_tenant_role_to_user.py` - PostgreSQL enum → no-op MySQL
- `03da7e1a34f5_add_exchange_rate_model.py` - gen_random_uuid() → UUID()
- `8f8548709ef9_fix_upgrade_requests_table.py` - Índice redundante → no-op

**Scripts de corrección:**
- Ejecutado fix_py39.py y fix_all_py39.py para convertir type hints
- Actualizado alembic.ini con DATABASE_URL de MySQL

### Verificación del Sistema

```bash
# Verificar que uvicorn está corriendo
ps aux | grep uvicorn

# Verificar conexión a BD
curl http://127.0.0.1:8000/health

# Probar login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "admin@jads.com", "password": "admin123456"}'

# Ver logs de uvicorn
tail -f /tmp/uvicorn.log 2>/dev/null || ps aux | grep uvicorn
```

### Comandos Útiles

```bash
# Reiniciar uvicorn
ssh -p 65002 u938946830@217.65.147.159 \
  'pkill -f "python3 -m uvicorn" && \
   sleep 2 && \
   cd /home/u938946830/jadslink-deploy/api && \
   nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 &'

# Ver logs de aplicación
ssh -p 65002 u938946830@217.65.147.159 'tail -f /tmp/uvicorn.log'

# Ejecutar migraciones (si es necesario)
ssh -p 65002 u938946830@217.65.147.159 \
  'cd /home/u938946830/jadslink-deploy/api && python3 -m alembic upgrade head'
```

## Notas Importantes

1. **No usar `localhost`**: MySQL en Hostinger solo acepta conexiones desde `127.0.0.1` (IPv4)
2. **Variable de entorno .env**: Ya está configurado en `/home/u938946830/jadslink-deploy/api/.env`
3. **PORT 8000**: Es interno a Hostinger, el acceso público es a través del reverse proxy
4. **Redis**: No está disponible en Hostinger (sistema funciona sin cache)
5. **Email**: No está configurado (puede agregarse después con Resend/SendGrid)

## Troubleshooting

**Error "Cannot drop index"**: MySQL no permite eliminar índices que son usados por foreign keys
**Error "Python type | None"**: Solo Python 3.10+ soporta esta sintaxis (Hostinger 3.9)
**Error "gen_random_uuid"**: PostgreSQL specific, MySQL usa UUID()
**Error "Connection refused 127.0.0.1:8000"**: Uvicorn no está corriendo, reiniciarlo

## Acceso a Documentación API
Una vez que Nginx está configurado correctamente:
- Docs: https://wheat-pigeon-347024.hostingersite.com/docs
- ReDoc: https://wheat-pigeon-347024.hostingersite.com/redoc

---

**Fecha de despliegue**: 2026-04-28
**Versión**: JADSlink 1.0 - MySQL Edition
**Ambiente**: Hostinger Shared Hosting
