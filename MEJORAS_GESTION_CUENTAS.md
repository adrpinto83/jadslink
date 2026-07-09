# Mejoras en Gestión de Cuentas - JADSlink

**Fecha**: 2026-07-05
**Versión**: v1.1.0

---

## 🎯 Funcionalidades Implementadas

### 1. ✅ Eliminar Cuentas (Soft Delete)
- **Función**: `deleteAccount(id, name)`
- **Características**:
  - Modal de confirmación profesional (no alert/confirm)
  - Soft delete: preserva datos para auditoría
  - Los usuarios no pueden iniciar sesión
  - Badge "Eliminada" en la tabla
  - Estilo visual diferenciado (opacity + fondo rojo)

**Uso**:
```javascript
// Llamado desde botón en tabla de cuentas
<button onclick="deleteAccount('${id}','${name}')">
  <i class="fa-solid fa-trash"></i>
</button>
```

### 2. ✅ Restaurar Cuentas
- **Función**: `restoreAccount(id)`
- **Características**:
  - Modal de confirmación
  - Restaura deleted_at a NULL
  - Los usuarios pueden volver a usar el sistema
  - Toast de confirmación visual

**Uso**:
```javascript
// Botón aparece solo para cuentas eliminadas
<button onclick="restoreAccount('${id}')">
  <i class="fa-solid fa-rotate-left"></i>
</button>
```

### 3. ✅ Otorgar Tickets Bonus
- **Función**: `grantTickets(id, name)`
- **Características**:
  - Modal profesional con form
  - Input de cantidad (default: 100)
  - Input de nota opcional
  - Valida cantidad > 0
  - Toast de éxito con cantidad otorgada
  - Se suma a `bonus_tickets` de la cuenta

**Uso**:
```javascript
<button onclick="grantTickets('${id}','${name}')">
  <i class="fa-solid fa-gift"></i>
</button>
```

### 4. ✅ Confirmación al Cambiar Plan/Estado
- **Función**: `updateAccount(id, field, value)`
- **Características**:
  - Modal de confirmación antes de aplicar el cambio
  - Muestra el nuevo valor en el modal
  - Si cancela, recarga la tabla (restaura valor anterior del select)
  - Si confirma, aplica el cambio y muestra toast de éxito

**Uso**:
```javascript
// Llamado desde select en tabla
<select onchange="updateAccount('${id}','plan',this.value)">
  <option>trial</option>
  <option>starter</option>
  ...
</select>
```

---

## 🎨 Componentes UI Agregados

### Modal de Confirmación
**ID**: `modal-confirm`

**Estructura**:
```html
<div id="modal-confirm" class="modal hidden">
  <div class="modal-content">
    <h3 id="confirm-title">Confirmar</h3>
    <div id="confirm-message"></div>
    <div class="modal-actions">
      <button onclick="confirmAction()">Confirmar</button>
      <button onclick="cancelAction()">Cancelar</button>
    </div>
  </div>
</div>
```

**Funciones**:
- `showConfirmModal(title, message, onConfirm, onCancel)`
- `confirmAction()`
- `cancelAction()`

### Modal de Otorgar Tickets
**ID**: `modal-grant-tickets`

**Estructura**:
```html
<div id="modal-grant-tickets" class="modal hidden">
  <div class="modal-content">
    <h3>Otorgar tickets bonus</h3>
    <p>Cuenta: <strong id="grant-account-name"></strong></p>
    <input type="number" id="grant-qty" value="100">
    <input type="text" id="grant-note" placeholder="Nota opcional">
    <button onclick="submitGrantTickets()">Otorgar</button>
  </div>
</div>
```

**Funciones**:
- `grantTickets(id, name)` - Abre el modal
- `submitGrantTickets()` - Envía la petición

### Sistema de Toasts
**Función**: `showToast(message, type)`

**Características**:
- Posición: fixed top-right
- Tipos: 'success' (verde) o 'error' (rojo)
- Animaciones: slideIn / slideOut
- Duración: 3 segundos
- Se auto-remueve del DOM

**Uso**:
```javascript
showToast('✓ Cuenta eliminada correctamente', 'success');
showToast('✗ Cantidad inválida', 'error');
```

**Estilos CSS**:
```css
@keyframes slideIn {
  from { transform: translateX(400px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes slideOut {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(400px); opacity: 0; }
}
```

---

## 📊 Tabla de Cuentas Mejorada

### Columnas

| Columna | Contenido | Características |
|---------|-----------|-----------------|
| **Cuenta** | Nombre + slug | Badge "Eliminada" si deleted_at |
| **Plan** | Select dropdown | Llama updateAccount() on change |
| **Estado** | Select dropdown | Llama updateAccount() on change |
| **Routers** | Cantidad / máximo | Ingresos mensuales en muted |
| **Tickets** | Disponibles / usados | Badge "ilimitados" si plan business |
| **Creada** | Fecha formateada | - |
| **Acciones** | Botones | Otorgar / Eliminar o Restaurar |

### Botones de Acción

**Cuenta activa**:
- 🎁 **Otorgar tickets** (`grantTickets`)
- 🗑️ **Eliminar** (`deleteAccount`) - Color rojo

**Cuenta eliminada**:
- ↩️ **Restaurar** (`restoreAccount`) - Color verde

### Visualización de Cuotas

**Plan con cuota limitada**:
```
45 disp. +10      ← 45 disponibles + 10 bonus
15/50 usados      ← 15 usados de 50 del plan mensual
```

**Plan ilimitado (business)**:
```
[ilimitados]      ← Badge verde
```

---

## 🔧 Archivos Modificados

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `frontend/static/js/app.js` | +145 líneas | 1530 |
| `frontend/static/css/app.css` | +25 líneas | 2274 |
| `frontend/index.html` | +39 líneas | 1143 |

### frontend/static/js/app.js
**Funciones agregadas**:
- `showToast(message, type)`
- `showConfirmModal(title, message, onConfirm, onCancel)`
- `confirmAction()`
- `cancelAction()`
- `submitGrantTickets()`

**Funciones mejoradas** (reemplazadas):
- `deleteAccount(id, name)` - Ahora usa modal
- `restoreAccount(id)` - Ahora usa modal con nombre
- `grantTickets(id, name)` - Ahora abre modal en lugar de prompt
- `updateAccount(id, field, value)` - Ahora pide confirmación

### frontend/static/css/app.css
**Estilos agregados**:
- `@keyframes slideIn`
- `@keyframes slideOut`

### frontend/index.html
**Modales agregados**:
- `#modal-confirm` - Modal de confirmación genérico
- `#modal-grant-tickets` - Modal para otorgar tickets

---

## 🚀 Deployment

### Archivos Actualizados en Hostinger

**Código fuente** (`~/jadslink-app/frontend/`):
```bash
✓ static/js/app.js (66KB)
✓ static/css/app.css (55KB)
✓ index.html (1143 líneas)
```

**Producción web** (`~/domains/jadsstudio.com/public_html/link/`):
```bash
✓ static/js/app.js?v=1783264000
✓ static/css/app.css?v=1783264000
✓ index.html
```

### Versión del Cache
- **Anterior**: v=1783250272
- **Nueva**: v=1783264000 ✅
- **Método**: Timestamp automático con `date +%s`

---

## 📝 Flujo de Usuario

### Eliminar una Cuenta

1. Superadmin hace clic en botón 🗑️ en tabla de cuentas
2. Aparece modal de confirmación:
   > **¿Eliminar cuenta?**
   >
   > ¿Estás seguro de eliminar la cuenta "Transportes ABC"?
   >
   > _Los usuarios no podrán acceder, pero los datos se preservan para auditoría._
   >
   > [Confirmar] [Cancelar]

3. Si confirma:
   - Se ejecuta `DELETE /api/accounts/{id}`
   - Toast verde: "✓ Cuenta eliminada correctamente"
   - Se recarga la tabla
   - La cuenta aparece con badge "Eliminada" y fondo rojo

### Restaurar una Cuenta

1. Superadmin activa checkbox "Mostrar eliminadas"
2. Cuentas eliminadas aparecen con badge y fondo rojo
3. Hace clic en botón ↩️
4. Modal de confirmación:
   > **¿Restaurar cuenta?**
   >
   > ¿Restaurar la cuenta "Transportes ABC"?
   >
   > _Los usuarios podrán volver a iniciar sesión y usar sus servicios._

5. Si confirma:
   - Se ejecuta `POST /api/accounts/{id}/restore`
   - Toast verde: "✓ Cuenta restaurada correctamente"
   - La cuenta vuelve a estado normal

### Otorgar Tickets Bonus

1. Superadmin hace clic en botón 🎁
2. Aparece modal con form:
   > **Otorgar tickets bonus**
   >
   > Cuenta: **Transportes ABC**
   >
   > Cantidad de tickets: [100]
   >
   > Nota (opcional): [Regalo por renovación anual]
   >
   > [🎁 Otorgar tickets] [Cancelar]

3. Si confirma:
   - Se ejecuta `POST /api/accounts/{id}/tickets/grant`
   - Toast verde: "✓ 100 tickets otorgados a Transportes ABC"
   - Se actualiza columna de tickets en la tabla

### Cambiar Plan o Estado

1. Superadmin cambia valor en select de Plan o Estado
2. Modal de confirmación:
   > **Confirmar cambio**
   >
   > ¿Cambiar el plan de esta cuenta?
   >
   > _Nuevo valor: **pro**_
   >
   > [Confirmar] [Cancelar]

3. Si confirma:
   - Se ejecuta `PATCH /api/accounts/{id}`
   - Toast verde: "✓ Plan actualizado"

4. Si cancela:
   - Se recarga la tabla (restaura valor anterior del select)

---

## 🎨 Mejoras de UX

### Antes (alert/confirm/prompt)
```javascript
// ❌ Antiguo
if (!confirm("¿Eliminar?")) return;
await api("DELETE", `/api/accounts/${id}`);
alert("Cuenta eliminada");
```

### Ahora (modales profesionales)
```javascript
// ✅ Nuevo
showConfirmModal(
  '¿Eliminar cuenta?',
  `¿Estás seguro de eliminar la cuenta "<strong>${name}</strong>"?<br><br>
  <span style="color:var(--muted);font-size:13px">
  Los usuarios no podrán acceder, pero los datos se preservan para auditoría.
  </span>`,
  async () => {
    const r = await api('DELETE', `/api/accounts/${id}`);
    if (r && r.ok) {
      showToast('✓ Cuenta eliminada correctamente', 'success');
      loadAccounts();
    }
  }
);
```

### Ventajas
- ✅ Modales consistentes con el diseño de la app
- ✅ HTML en mensajes (negritas, colores, line breaks)
- ✅ Callbacks asíncronos
- ✅ Cancelación sin reload
- ✅ Toasts animados en lugar de alerts
- ✅ Mejor feedback visual

---

## 🔒 Seguridad

### Validaciones Implementadas

1. **Solo superadmin** puede:
   - Eliminar cuentas
   - Restaurar cuentas
   - Otorgar tickets bonus
   - Cambiar plan/estado

2. **Soft delete**:
   - `deleted_at` se llena con timestamp
   - `deleted_by` guarda ID del superadmin que eliminó
   - Datos preservados para auditoría

3. **Validación de inputs**:
   - Cantidad de tickets > 0
   - Selects deshabilitados para cuentas eliminadas

---

## 📊 Métricas de Uso

### Endpoints del Backend

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/accounts/{id}` | DELETE | Eliminar cuenta (soft) |
| `/api/accounts/{id}/restore` | POST | Restaurar cuenta |
| `/api/accounts/{id}/tickets/grant` | POST | Otorgar tickets bonus |
| `/api/accounts/{id}` | PATCH | Actualizar plan/estado |
| `/api/accounts?include_deleted=true` | GET | Listar con eliminadas |

### Logs de Auditoría

Tabla `ticket_quota_logs`:
```sql
SELECT * FROM ticket_quota_logs
WHERE action = 'grant_bonus'
ORDER BY created_at DESC;
```

Muestra:
- Quién otorgó tickets
- Cuántos
- A qué cuenta
- Nota explicativa
- Timestamp

---

## ✅ Checklist de Verificación

- [x] Modal de confirmación funciona
- [x] Modal de otorgar tickets funciona
- [x] Toasts se muestran correctamente
- [x] Animaciones slideIn/slideOut funcionan
- [x] Botones en tabla correctos (eliminar/restaurar)
- [x] Checkbox "Mostrar eliminadas" funciona
- [x] Cuentas eliminadas tienen estilo diferenciado
- [x] Confirmación al cambiar plan/estado
- [x] Versión de JS actualizada (v=1783264000)
- [x] Archivos copiados a producción web
- [x] Código sincronizado en jadslink-app

---

## 🎓 Próximos Pasos

### Mejoras Sugeridas

1. **Historial de cambios**:
   - Tabla `account_audit_log`
   - Registrar cambios de plan, estado, eliminación, restauración

2. **Filtros en tabla de cuentas**:
   - Por plan
   - Por estado
   - Por uso de cuota

3. **Exportar datos**:
   - CSV de cuentas
   - PDF de reporte

4. **Notificaciones por email**:
   - Al eliminar cuenta
   - Al restaurar cuenta
   - Al otorgar tickets

---

**Implementado**: 2026-07-05
**Versión**: v1.1.0
**Estado**: ✅ En producción
