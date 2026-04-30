# 🚀 DEPLOYMENT: Planes SaaS en Hostinger

**Fecha**: 2026-04-30
**Script**: `deploy-saas-plans.sh`
**Tiempo estimado**: 10-15 minutos
**Riesgo**: Muy bajo (con backup automático)

---

## 📋 PRE-REQUISITOS

Antes de ejecutar el script, verifica:

- [ ] Tienes acceso SSH a Hostinger
- [ ] El repositorio está clonado en `/home/adrpinto/jadslink`
- [ ] Los cambios están pusheados a Git
- [ ] La BD está accesible (MySQL/PostgreSQL)
- [ ] El API está corriendo en puerto 8000
- [ ] Tienes permisos de `sudo` (para reiniciar servicios)

---

## 🔧 OPCIÓN 1: Vía SSH (RECOMENDADO)

### 1. Conectarse a Hostinger

```bash
ssh usuario@tu-servidor-hostinger.com
```

### 2. Navegar al directorio del proyecto

```bash
cd /home/adrpinto/jadslink
```

### 3. Asegurarse que está en la rama main con cambios más recientes

```bash
git status
git pull origin main
```

### 4. Ejecutar el script de deployment

```bash
./deploy-saas-plans.sh
```

**Espera a que finalice (~10 minutos)**

### 5. Verificar que todo funcionó

```bash
# En el mismo servidor:
curl http://localhost:8000/api/v1/saas-plans | jq '.[] | {tier, name, monthly_price}'
```

**Debería mostrar:**
```json
{
  "tier": "free",
  "name": "Gratuito",
  "monthly_price": 0
}
{
  "tier": "basic",
  "name": "Básico",
  "monthly_price": 29
}
```

---

## 🔧 OPCIÓN 2: Paso a Paso Manual (SI EL SCRIPT FALLA)

### 1. Conectarse al servidor

```bash
ssh usuario@tu-servidor-hostinger.com
cd /home/adrpinto/jadslink
```

### 2. Hacer backup

```bash
mkdir -p backups
DATE=$(date +"%Y%m%d_%H%M%S")
mysqldump -u usuario -p tu_base_datos > backups/backup_$DATE.sql
```

### 3. Ejecutar migración

```bash
cd api
python3 -m alembic upgrade head
```

Debería ver:
```
INFO [alembic.runtime.migration] Running upgrade ... -> ..., create_pricing_plans_table
INFO [alembic.migration] Done.
```

### 4. Insertar los 4 planes

```bash
cd ..
python3 api/scripts/seed_pricing_plans.py
```

Debería ver:
```
✅ 4 planes SaaS creados exitosamente:
   • Gratuito: $0 (50 tickets/mes)
   • Básico: $29 (200 tickets/mes)
   • Estándar: $79 (1,000 tickets/mes, 3 nodos) [RECOMENDADO]
   • Pro: $199 (Ilimitado)
```

### 5. Verificar planes en BD

```bash
mysql -u usuario -p tu_base_datos -e \
  "SELECT tier, name, monthly_price FROM pricing_plans ORDER BY sort_order;"
```

### 6. Reiniciar API

**Opción A: Systemd**
```bash
sudo systemctl restart jadslink-api
```

**Opción B: PM2**
```bash
pm2 restart api
pm2 save
```

**Opción C: Docker**
```bash
docker-compose restart api
```

### 7. Probar endpoint

```bash
curl http://localhost:8000/api/v1/saas-plans | jq '.' | head -20
```

---

## 🔧 OPCIÓN 3: Vía cPanel (SI NO TIENES SSH)

Si Hostinger no te da acceso SSH directo, usa cPanel:

### 1. File Manager
- Abre File Manager en cPanel
- Navega a `/home/adrpinto/jadslink`
- Verifica que los archivos nuevos estén allí:
  - `api/models/pricing_plan.py`
  - `api/routers/plans_saas.py`
  - `api/scripts/seed_pricing_plans.py`
  - `api/migrations/versions/a7c2f8d9e4b1_*.py`

### 2. Terminal en cPanel
- Ve a "Terminal" en cPanel
- Ejecuta los mismos comandos que en SSH

```bash
cd /home/adrpinto/jadslink
./deploy-saas-plans.sh
```

### 3. Monitorear ejecución
- Los logs aparecerán en la terminal
- Espera a que se complete

---

## 🔧 OPCIÓN 4: Vía Git Push (SI TIENES CI/CD)

Si tienes GitHub Actions u otro CI/CD configurado:

### 1. Hacer push a rama de staging/test

```bash
git push origin main
```

### 2. El CI/CD ejecutará automáticamente

Si tienes un workflow en `.github/workflows/`, puede ejecutar el script automáticamente.

### 3. Monitorear en GitHub

- Ve a "Actions" en tu repositorio
- Ve el workflow ejecutándose
- Verifica que pase sin errores

---

## ⚠️ TROUBLESHOOTING

### Error: "Tabla pricing_plans ya existe"

```bash
# Si la tabla ya existe, Alembic lo detectará y saltará el paso
# Continúa al paso de seed
```

### Error: "4 planes ya existen en BD"

```bash
# El script detectará esto y eliminará los antiguos antes de insertar nuevos
# Es seguro ejecutarlo múltiples veces
```

### Error: "ModuleNotFoundError: alembic"

```bash
# Instalar dependencias
pip install alembic sqlalchemy aiomysql --break-system-packages

# O mejor, crear virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Conexión a BD rechazada"

```bash
# Verificar credenciales en .env
cat .env | grep DATABASE_URL

# Verificar que BD está corriendo
mysql -u usuario -h localhost -p -e "SELECT 1"
```

### Endpoint no responde (HTTP 000)

```bash
# Verificar que API está corriendo
ps aux | grep uvicorn
ps aux | grep pm2
docker ps | grep api

# Si no está corriendo, iniciar
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Login/Billing no muestra planes

```bash
# Limpiar cache del navegador
# F12 → Application → Storage → Clear Site Data

# Verificar CORS
curl -i http://localhost:8000/api/v1/saas-plans

# Verificar en DevTools console para errores 403
```

---

## ✅ CHECKLIST POST-DEPLOYMENT

Después de ejecutar el script, verifica:

### Base de Datos
- [ ] Tabla `pricing_plans` existe
- [ ] Contiene 4 registros
- [ ] Precios correctos: $0, $29, $79, $199
- [ ] Plan "standard" tiene is_recommended=1

### API
- [ ] Endpoint `/api/v1/saas-plans` accesible
- [ ] Retorna JSON con 4 planes
- [ ] No hay errores en logs

### Frontend - Login
- [ ] Abre `https://tu-dominio.com/login`
- [ ] Ver 4 planes en grid
- [ ] Plan "Estándar" tiene badge "Más Popular"
- [ ] Plan "Estándar" está más grande

### Frontend - Billing
- [ ] Abre `https://tu-dominio.com/dashboard/billing`
- [ ] Ver 4 planes dinámicos
- [ ] Features vienen desde BD (no hardcoded)

### Frontend - Admin
- [ ] Abre `https://tu-dominio.com/dashboard/admin/subscriptions`
- [ ] Select de planes incluye "ESTÁNDAR"

---

## 📊 QUÉ HACE EL SCRIPT

El script `deploy-saas-plans.sh` ejecuta automáticamente:

```
1. ✅ Verificaciones iniciales
   - Directorios existen
   - BD accesible

2. ✅ Crear backup
   - mysqldump de BD actual
   - Guardado en backups/

3. ✅ Git pull
   - Obtener cambios más recientes

4. ✅ Migración Alembic
   - python3 -m alembic upgrade head
   - Crea tabla pricing_plans

5. ✅ Seed de planes
   - Ejecuta script seed_pricing_plans.py
   - Inserta 4 planes en BD

6. ✅ Verificación
   - Comprueba que planes están en BD
   - Valida estructura

7. ✅ Endpoint test
   - Prueba GET /api/v1/saas-plans

8. ✅ Reinicio API
   - systemd / pm2 / docker

9. ✅ Verificación final
   - Checklist de 8 items
```

---

## 🔄 ROLLBACK (SI ALGO SALE MAL)

Si algo falla, puedes revertir:

### Opción 1: Desde backup automático

```bash
# El script crea backup automático antes de cambios
mysql -u usuario -p tu_base_datos < backups/jads_before_saas_plans_YYYYMMDD_HHMMSS.sql
```

### Opción 2: Revertir migración Alembic

```bash
cd api
python3 -m alembic downgrade -1
```

### Opción 3: Git revert

```bash
git revert HEAD
git push origin main
```

---

## 📞 SOPORTE

Si encuentras problemas:

1. **Consultar logs**
   ```bash
   tail -f /var/log/jadslink-api.log
   # O para pm2
   pm2 logs api
   ```

2. **Leer documentación**
   - `MIGRACION_PLANES_SAAS.md`
   - `IMPLEMENTACION_PLANES_SAAS_FINAL.md`

3. **Verificar BD manualmente**
   ```bash
   mysql -u usuario -p tu_base_datos
   > SELECT * FROM pricing_plans;
   ```

4. **Verificar código**
   - `api/models/pricing_plan.py`
   - `api/routers/plans_saas.py`

---

## 🎉 RESULTADO ESPERADO

Después de ejecutar el script exitosamente:

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        ✅ DEPLOYMENT COMPLETADO EN HOSTINGER                  ║
║                                                                ║
║  ✅ Migración Alembic ejecutada                               ║
║  ✅ 4 planes insertados en BD                                 ║
║  ✅ Endpoint /api/v1/saas-plans activo                        ║
║  ✅ API reiniciada                                            ║
║  ✅ Todas las verificaciones pasaron                          ║
║                                                                ║
║  💰 PLANES DISPONIBLES:                                        ║
║     • Gratuito: $0/mes                                         ║
║     • Básico: $29/mes                                          ║
║     • Estándar: $79/mes ⭐                                     ║
║     • Pro: $199/mes                                            ║
║                                                                ║
║  🔗 Accesos:                                                   ║
║     API: https://tu-dominio.com/api/v1/saas-plans             ║
║     Dashboard: https://tu-dominio.com                          ║
║                                                                ║
║  ✨ ¡Todo listo para producción!                              ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 📝 NOTAS IMPORTANTES

- El script es **idempotente**: puedes ejecutarlo múltiples veces sin problema
- Crea **backup automático** antes de cambios
- **No borra datos**, solo agrega tabla nueva
- Compatible con MySQL y PostgreSQL
- Soporta systemd, pm2 y Docker

---

**Última actualización**: 2026-04-30
**Script**: `deploy-saas-plans.sh`
**Estado**: ✅ LISTO PARA HOSTINGER
