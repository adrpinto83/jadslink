# Workflow de Sincronización JADSlink

## Estado Actual

- **Producción**: Hostinger (`~/jadslink-app`)
- **Desarrollo Local**: `/home/adrpinto/jadslink/jadslink-app/`
- **GitHub**: `https://github.com/adrpinto83/jadslink` (rama `feature/vendor-jadslink-app-and-pg-migration`)

## Sincronización Local → GitHub → Hostinger

### 1. Desde Local (después de hacer cambios)

```bash
cd /home/adrpinto/jadslink
git add -A
git commit -m "descripción del cambio"
git push origin feature/vendor-jadslink-app-and-pg-migration
```

### 2. Desde Hostinger (descargar cambios)

```bash
ssh -p 65002 u938946830@217.65.147.159
cd ~/jadslink-app

# Hacer backup antes de actualizar
tar -czf ../backup-$(date +%Y%m%d-%H%M%S).tar.gz .

# Descargar cambios (si hay conflictos, resolverlos manualmente)
git stash  # guardar cambios locales si los hay
git pull origin feature/vendor-jadslink-app-and-pg-migration
git stash pop  # recuperar cambios locales

# Reiniciar uvicorn
pkill -f 'uvicorn api.main'
# El proxy PHP lo reiniciará automáticamente en la próxima petición
```

## Sincronización Hostinger → Local (código actualizado en producción)

### Desde Local

```bash
cd /home/adrpinto/jadslink

# Descargar código actual de Hostinger
ssh -p 65002 u938946830@217.65.147.159 "cd ~/jadslink-app && tar -czf - api frontend passenger_wsgi.py requirements.txt .env" | tar -xzf - -C jadslink-app/

# Revisar cambios
git status
git diff

# Commit y push
git add -A
git commit -m "sync: actualizar desde Hostinger"
git push origin feature/vendor-jadslink-app-and-pg-migration
```

## Archivos Importantes

### NO versionados (en .gitignore):
- `venv/` - Entorno virtual Python
- `*.db` - Bases de datos SQLite
- `*.log` - Logs
- `.env` - Variables de entorno (mantener separado por ambiente)
- `__pycache__/` - Cache de Python

### Versionados:
- `api/` - Código backend FastAPI
- `frontend/` - HTML/CSS/JS del dashboard
- `requirements.txt` - Dependencias Python
- `passenger_wsgi.py` - Configuración WSGI

## Backup Manual

```bash
# En Hostinger
ssh -p 65002 u938946830@217.65.147.159
cd ~
tar -czf jadslink-backup-$(date +%Y%m%d-%H%M%S).tar.gz jadslink-app/
ls -lh jadslink-backup-*.tar.gz
```

## Verificar Estado

```bash
# Local
git status
git log --oneline -5

# Hostinger
ssh -p 65002 u938946830@217.65.147.159 "cd ~/jadslink-app && git status && git log --oneline -5"
```

## Notas

- **Fuente de verdad**: Hostinger tiene el código funcional actual
- **Desarrollo**: Hacer cambios en local, probar, luego subir
- **Deploy**: Siempre hacer backup antes de actualizar producción
- **Conflictos**: Si hay conflictos, revisar manualmente antes de sobrescribir

---
Última actualización: 2026-07-05
