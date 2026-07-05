# Análisis de Diferencias: jadslink-hostinger vs Hostinger

**Fecha**: 2026-07-05
**Contexto**: Comparación entre backup local (`~/jadslink-hostinger`) y producción (`~/jadslink-app`)

---

## 📊 Resumen Ejecutivo

Se encontraron **diferencias críticas** entre el backup local y la producción:

1. ✅ **Landing page completa** existía en backup pero NO en producción
2. ⚠️ **CSS 10x más grande** en backup (2249 líneas vs 229 líneas)
3. ⚠️ **JavaScript con 167 líneas extras** en backup
4. 📦 **Archivos obsoletos** en backup (versiones antiguas del dashboard)

---

## 🔍 Archivos que EXISTEN en jadslink-hostinger pero NO en Hostinger

### 1. `api/routes/index.html` (20KB, 399 líneas)
**Tipo**: Dashboard HTML antiguo
**Descripción**: Versión anterior del dashboard que solo incluye login + panel administrativo (sin landing page)
**Estado**: ⚠️ **OBSOLETO** (reemplazado por `frontend/index.html`)
**Acción**: Se puede eliminar del backup

### 2. `api/routes/app.js` (31KB, 693 líneas)
**Tipo**: JavaScript del dashboard antiguo
**Descripción**: Lógica JS del dashboard antiguo
**Estado**: ⚠️ **OBSOLETO** (reemplazado por `frontend/static/js/app.js`)
**Acción**: Se puede eliminar del backup

---

## 🆕 Archivos que EXISTEN en Hostinger pero NO en jadslink-hostinger

### 1. `api/quota.py`
**Tipo**: Módulo Python para sistema de cuotas
**Descripción**: Sistema de cuotas de tickets por plan (implementado hoy 2026-07-05)

**Funciones principales**:
```python
def can_generate_tickets(db, account, quantity) -> (bool, str)
def consume_tickets(db, account, quantity)
def grant_bonus_tickets(db, account, quantity, granted_by, note)
def reset_monthly_quota(db)
```

**Estado**: ✅ **NUEVO** (parte del sistema de gestión de cuentas)
**Acción**: Necesita sincronizarse al backup local

---

## 📝 Diferencias en archivos existentes en AMBOS

### 1. `frontend/index.html`

| Versión | Líneas | Contenido | Timestamp |
|---------|--------|-----------|-----------|
| **jadslink-hostinger** | 1110 | Landing + Login + Dashboard | 1783250272 |
| **Hostinger (antes)** | ~800 | Login + Dashboard (SIN landing) | - |
| **Hostinger (ahora)** | 1110 | ✅ **ACTUALIZADO** | 1783250272 |

**Diferencias clave**:
- ✅ Landing page completa con secciones:
  - Hero section con CTA
  - Casos de uso (4 cards con imágenes)
  - Cómo funciona (4 pasos)
  - JADSLink en acción (galería 3 imágenes)
  - Beneficios (6 items)
  - CTA final
  - Footer
- ✅ Formularios de login y signup mejorados
- ✅ Gestión de múltiples "screens" (landing, login, dashboard)

**Estado**: ✅ **RESTAURADO** en producción

---

### 2. `frontend/static/js/app.js`

| Versión | Líneas | Tamaño | Funcionalidad |
|---------|--------|--------|---------------|
| **jadslink-hostinger** | 1557 | ~70KB | Completo con landing |
| **Hostinger (antes)** | 1390 | ~62KB | Sin código de landing |
| **Hostinger (ahora)** | 1557 | ✅ **ACTUALIZADO** | Completo |

**Diferencia**: 167 líneas adicionales

**Funciones adicionales en versión completa**:
```javascript
function showLogin()       // Cambiar a pantalla de login
function showSignup()      // Cambiar a pantalla de signup
function showDashboard()   // Cargar dashboard tras login
// Gestión de navegación entre screens
// Animaciones y efectos de landing
// Validación de formularios mejorada
```

**Estado**: ✅ **ACTUALIZADO** en producción

---

### 3. `frontend/static/css/app.css`

| Versión | Líneas | Diferencia | Estado |
|---------|--------|------------|--------|
| **jadslink-hostinger** | 2249 | - | Completo |
| **Hostinger (antes)** | 229 | -2020 líneas | Mínimo |
| **Hostinger (ahora)** | 2249 | ✅ **ACTUALIZADO** | Completo |

**Diferencia crítica**: ⚠️ **10x más código CSS**

**Estilos adicionales incluyen**:
- Landing page completa (header, hero, sections, gallery, footer)
- Responsive design mejorado
- Animaciones y transiciones
- Cards de casos de uso con imágenes
- Galería de imágenes con overlays
- Tema claro/oscuro completo
- Formularios mejorados con validación visual

**Estado**: ✅ **ACTUALIZADO** en producción

---

## 🎯 Acciones Realizadas

### 1. ✅ Restauración de landing page
```bash
# Copiar index.html a producción web
scp ~/jadslink-hostinger/frontend/index.html → ~/domains/.../link/

# Copiar archivos static
scp -r ~/jadslink-hostinger/frontend/static/ → ~/domains/.../link/

# Actualizar .htaccess para routing
# Renombrar index.php → app.php
```

### 2. ✅ Sincronización de código fuente
```bash
# Actualizar jadslink-app/frontend/ para consistencia
cp ~/domains/.../link/index.html → ~/jadslink-app/frontend/
cp ~/domains/.../link/static/* → ~/jadslink-app/frontend/static/
```

### 3. ✅ Versionado en Git
```bash
# Agregar landing/ al repositorio
mkdir landing/
cp index.html + static/ → landing/
git add landing/ LANDING_STRUCTURE.md
git commit -m "feat(landing): restaurar landing page de JADSLink"
git push
```

---

## 📍 Estado Actual

### Producción Web (https://link.jadsstudio.com/)
- ✅ Landing page completa funcionando
- ✅ CSS completo (2249 líneas)
- ✅ JavaScript completo (1557 líneas)
- ✅ Routing configurado (.htaccess)
  - `/` → Landing page
  - `/app` → Panel administrativo
  - `/api/*` → API FastAPI

### Código Fuente (~/jadslink-app)
- ✅ frontend/index.html actualizado (1110 líneas)
- ✅ frontend/static/js/app.js actualizado (1557 líneas)
- ✅ frontend/static/css/app.css actualizado (2249 líneas)
- ✅ Consistencia con producción web

### Repositorio Git
- ✅ landing/ versionado
- ✅ LANDING_STRUCTURE.md documentado
- ✅ Sincronizado con GitHub

---

## ⚠️ Archivos Obsoletos en Backup

Estos archivos están en `~/jadslink-hostinger` pero son versiones antiguas:

1. `api/routes/index.html` (399 líneas)
2. `api/routes/app.js` (693 líneas)

**Recomendación**: Pueden eliminarse del backup ya que han sido reemplazados por versiones superiores en `frontend/`.

---

## 🔄 Archivos Faltantes en Backup

Estos archivos están en producción pero NO en el backup:

1. `api/quota.py` (sistema de cuotas implementado hoy)

**Recomendación**: Sincronizar desde Hostinger al backup local:
```bash
scp -P 65002 u938946830@217.65.147.159:~/jadslink-app/api/quota.py ~/jadslink-hostinger/api/
```

---

## 📊 Estadísticas de Diferencias

| Archivo | Backup | Producción (antes) | Producción (ahora) | Estado |
|---------|--------|-------------------|-------------------|---------|
| `frontend/index.html` | 1110 líneas | ~800 líneas | 1110 líneas | ✅ Sincronizado |
| `frontend/static/js/app.js` | 1557 líneas | 1390 líneas | 1557 líneas | ✅ Sincronizado |
| `frontend/static/css/app.css` | 2249 líneas | 229 líneas | 2249 líneas | ✅ Sincronizado |
| `api/quota.py` | ❌ No existe | ✅ Existe | ✅ Existe | ⚠️ Falta en backup |

---

## 🎓 Lecciones Aprendidas

1. **El backup local tenía la versión correcta** de la landing page
2. **La sincronización inicial sobrescribió** archivos importantes
3. **Necesidad de proceso de deploy más robusto** para evitar pérdidas

### Mejora Propuesta: Workflow de Deploy

```bash
# 1. Backup ANTES de deploy
tar -czf backup-pre-deploy-$(date +%Y%m%d-%H%M%S).tar.gz ~/jadslink-app

# 2. Deploy selectivo (NO sobrescribir todo)
# Solo actualizar archivos específicos que cambiaron

# 3. Verificación post-deploy
curl https://link.jadsstudio.com/ | grep "Vende Internet"

# 4. Rollback automático si falla
if [ $? -ne 0 ]; then
    tar -xzf backup-pre-deploy-*.tar.gz
fi
```

---

**Conclusión**: Todas las diferencias críticas han sido identificadas y resueltas. La landing page está completamente restaurada y versionada.

---

**Última actualización**: 2026-07-05 14:30
**Autor**: Claude Sonnet 4.5
