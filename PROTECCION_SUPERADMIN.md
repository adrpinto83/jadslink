# Protección de Cuenta Superadmin - JADSlink

**Fecha**: 2026-07-05
**Versión**: v1.1.1

---

## 🛡️ Implementación

### Objetivo
Prevenir la eliminación accidental o intencional de la cuenta que contiene al usuario superadmin del sistema.

---

## 🔒 Validaciones Implementadas

### 1. Backend (API)

**Archivo**: `api/routes/accounts.py`
**Endpoint**: `DELETE /api/accounts/{account_id}`

**Validación agregada**:
```python
@router.delete("/accounts/{account_id}")
def delete_account(account_id: str, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    """Soft delete de una cuenta (solo superadmin)."""
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if acc.deleted_at is not None:
        raise HTTPException(status_code=400, detail="La cuenta ya está eliminada")

    # ✅ PROTECCIÓN: Prevenir eliminación de cuenta con usuarios superadmin
    has_superadmin = db.query(User).filter(
        User.account_id == account_id,
        User.role == "superadmin"
    ).first()
    if has_superadmin:
        raise HTTPException(status_code=403, detail="No se puede eliminar la cuenta del superadmin")

    from datetime import datetime
    acc.deleted_at = datetime.utcnow()
    acc.deleted_by = user.id
    db.commit()
    return {"ok": True, "message": f"Cuenta '{acc.name}' eliminada"}
```

**Respuesta de error**:
- **Código**: 403 Forbidden
- **Mensaje**: "No se puede eliminar la cuenta del superadmin"

---

### 2. Backend (Response)

**Archivo**: `api/routes/accounts.py`
**Función**: `_account_dict()`

**Campo agregado**:
```python
def _account_dict(a: Account, db: Session) -> dict:
    usage = billing.compute_usage(db, a)
    quota_info = quota.get_quota_info(db, a)

    # ✅ Identificar si la cuenta tiene usuarios superadmin
    has_superadmin = db.query(User).filter(
        User.account_id == a.id,
        User.role == "superadmin"
    ).first() is not None

    return {
        "id": a.id,
        "name": a.name,
        ...
        "has_superadmin": has_superadmin,  # ✅ Nuevo campo
    }
```

**Uso**:
- El frontend usa este campo para ocultar botones de acciones peligrosas
- Se devuelve en todos los endpoints que retornan cuentas

---

### 3. Frontend (UI)

**Archivo**: `frontend/static/js/app.js`
**Función**: `loadAccounts()`

**Lógica de botones**:
```javascript
const actionBtns = isDeleted
  // Si está eliminada → botón de restaurar
  ? `<button onclick="restoreAccount('${a.id}')">
       <i class="fa-solid fa-rotate-left"></i>
     </button>`
  // ✅ Si tiene superadmin → solo texto (sin botones)
  : a.has_superadmin
  ? `<span style="color:var(--muted);font-size:11px;font-style:italic">
       Cuenta del sistema
     </span>`
  // Si es cuenta normal → botones de otorgar y eliminar
  : `<button onclick="grantTickets('${a.id}','${a.name}')">
       <i class="fa-solid fa-gift"></i>
     </button>
     <button onclick="deleteAccount('${a.id}','${a.name}')">
       <i class="fa-solid fa-trash"></i>
     </button>`;
```

**Resultado visual**:
- **Cuenta normal**: Botones 🎁 Otorgar y 🗑️ Eliminar
- **Cuenta con superadmin**: Texto "Cuenta del sistema" en cursiva gris
- **Cuenta eliminada**: Botón ↩️ Restaurar

---

## 🔍 Identificación de Cuenta Superadmin

### Criterios

Una cuenta se considera "cuenta del sistema" si cumple:

```sql
SELECT * FROM users
WHERE account_id = '{cuenta_id}'
  AND role = 'superadmin';
```

Si existe al menos un usuario con `role = 'superadmin'` vinculado a la cuenta, esta **NO puede ser eliminada**.

### Usuarios Superadmin

Características:
- `role = "superadmin"` (en tabla `users`)
- `account_id` puede ser NULL o apuntar a una cuenta específica
- Tienen acceso total al sistema
- Pueden gestionar todas las cuentas

---

## 🎯 Casos de Uso

### Caso 1: Intento de Eliminar Cuenta Normal
**Usuario**: Superadmin
**Acción**: Click en botón 🗑️ Eliminar de cuenta "Transportes ABC"
**Resultado**:
1. Modal de confirmación aparece
2. Usuario confirma
3. ✅ Cuenta eliminada (soft delete)
4. Toast verde: "✓ Cuenta eliminada correctamente"

---

### Caso 2: Intento de Eliminar Cuenta del Sistema
**Usuario**: Superadmin
**Acción**: Intenta eliminar cuenta con usuario superadmin
**Frontend**:
- ❌ Botón de eliminar NO aparece
- Muestra: "Cuenta del sistema" en gris

**Backend** (si se intenta via API directa):
```bash
curl -X DELETE https://link.jadsstudio.com/api/accounts/{id} \
  -H "Authorization: Bearer {token}"

# Response:
{
  "detail": "No se puede eliminar la cuenta del superadmin"
}
# Status: 403 Forbidden
```

---

### Caso 3: Listado de Cuentas

**Request**:
```javascript
GET /api/accounts
```

**Response**:
```json
[
  {
    "id": "acc-123",
    "name": "JADS Studio",
    "slug": "jads-studio",
    "status": "active",
    "plan": "business",
    "has_superadmin": true,     // ✅ Cuenta del sistema
    ...
  },
  {
    "id": "acc-456",
    "name": "Transportes ABC",
    "slug": "transportes-abc",
    "status": "active",
    "plan": "pro",
    "has_superadmin": false,    // ✅ Cuenta normal
    ...
  }
]
```

---

## 📊 Tabla de Cuentas - Visualización

| Cuenta | Plan | Estado | Routers | Tickets | Creada | Acciones |
|--------|------|--------|---------|---------|--------|----------|
| **JADS Studio** | business | active | 5 / ∞ | ilimitados | 2026-01-15 | _Cuenta del sistema_ |
| Transportes ABC | pro | active | 3 / 20 | 45 / 1000 | 2026-02-20 | 🎁 🗑️ |
| Eventos XYZ | starter | active | 1 / 5 | 80 / 200 | 2026-03-10 | 🎁 🗑️ |

**Nota**: La cuenta "JADS Studio" (o la que contenga al superadmin) NO tiene botones de acción, solo muestra "Cuenta del sistema".

---

## 🔧 Archivos Modificados

| Archivo | Cambios | Descripción |
|---------|---------|-------------|
| `api/routes/accounts.py` | +7 líneas | Validación en DELETE + campo has_superadmin |
| `frontend/static/js/app.js` | Modificado | Lógica condicional para botones |

### api/routes/accounts.py

**Líneas agregadas en `delete_account()`**:
```python
# Prevenir eliminación de cuenta con usuarios superadmin
has_superadmin = db.query(User).filter(
    User.account_id == account_id,
    User.role == "superadmin"
).first()
if has_superadmin:
    raise HTTPException(status_code=403, detail="No se puede eliminar la cuenta del superadmin")
```

**Líneas agregadas en `_account_dict()`**:
```python
has_superadmin = db.query(User).filter(
    User.account_id == a.id,
    User.role == "superadmin"
).first() is not None

return {
    ...
    "has_superadmin": has_superadmin,
}
```

### frontend/static/js/app.js

**Modificación en `loadAccounts()`**:
```javascript
// Antes:
const actionBtns = isDeleted
  ? `<button onclick="restoreAccount(...)">...</button>`
  : `<button onclick="grantTickets(...)">...</button>
     <button onclick="deleteAccount(...)">...</button>`;

// Después:
const actionBtns = isDeleted
  ? `<button onclick="restoreAccount(...)">...</button>`
  : a.has_superadmin  // ✅ Nueva condición
  ? `<span>Cuenta del sistema</span>`
  : `<button onclick="grantTickets(...)">...</button>
     <button onclick="deleteAccount(...)">...</button>`;
```

---

## ✅ Testing

### Test 1: Verificar Campo has_superadmin
```bash
curl https://link.jadsstudio.com/api/accounts \
  -H "Authorization: Bearer {token}"

# Verificar que cada cuenta tiene el campo has_superadmin: true/false
```

### Test 2: Intentar Eliminar Cuenta del Sistema
```bash
curl -X DELETE https://link.jadsstudio.com/api/accounts/{superadmin_account_id} \
  -H "Authorization: Bearer {token}"

# Esperado:
# Status: 403
# Body: {"detail": "No se puede eliminar la cuenta del superadmin"}
```

### Test 3: Eliminar Cuenta Normal
```bash
curl -X DELETE https://link.jadsstudio.com/api/accounts/{normal_account_id} \
  -H "Authorization: Bearer {token}"

# Esperado:
# Status: 200
# Body: {"ok": true, "message": "Cuenta 'XXX' eliminada"}
```

### Test 4: Verificar UI
1. Login como superadmin
2. Ir a sección "Cuentas"
3. Verificar que:
   - Cuenta con superadmin muestra "Cuenta del sistema" (sin botones)
   - Cuentas normales muestran botones 🎁 y 🗑️

---

## 🛡️ Seguridad

### Capas de Protección

1. **Backend**: Validación en endpoint DELETE
   - Si intento directo via API → 403 Forbidden
   - No se puede bypass con tokens o permisos

2. **Frontend**: Botón oculto
   - UX limpia (no muestra botón inútil)
   - Previene intentos accidentales

3. **Database**: Soft delete
   - Si de alguna forma se llegara a marcar como eliminada
   - Los datos siguen en BD y se pueden restaurar

### Auditoría

Si se intenta eliminar la cuenta superadmin, queda registrado en:
- Logs de FastAPI (uvicorn.log)
- Respuesta 403 con detalle específico

---

## 📝 Notas

### ¿Por qué no hacer account_id = NULL para superadmin?

Opción 1 (actual): Superadmin **puede** tener account_id
```
users:
  id=1, username="admin", role="superadmin", account_id="acc-jads"
```

Opción 2 (alternativa): Superadmin **siempre** account_id = NULL
```
users:
  id=1, username="admin", role="superadmin", account_id=NULL
```

**Razón de usar Opción 1**:
- Permite al superadmin tener su propia "cuenta" para pruebas
- Más flexible para multi-superadmin en el futuro
- La validación funciona igual (chequea `role == "superadmin"`, no `account_id`)

---

## 🎓 Mejoras Futuras

### Sugerencias

1. **Badge visual**: Agregar badge "Sistema" en la fila de la cuenta
2. **Tooltip**: Explicar por qué no se puede eliminar al pasar mouse
3. **Logs de auditoría**: Registrar intentos de eliminación bloqueados
4. **Protección de restauración**: Si se eliminó por error, requerir confirmación extra para restaurar
5. **Multi-superadmin**: Permitir múltiples cuentas del sistema

---

## 🚀 Deployment

### Archivos Actualizados

**Backend**:
```bash
✓ api/routes/accounts.py
```

**Frontend**:
```bash
✓ frontend/static/js/app.js
✓ frontend/index.html (versión v=1783264412)
```

**Producción**:
```bash
✓ ~/domains/jadsstudio.com/public_html/link/static/js/app.js
✓ ~/domains/jadsstudio.com/public_html/link/index.html
```

**Servicio**:
```bash
✓ uvicorn reiniciado
```

---

## ✅ Checklist de Verificación

- [x] Backend: Validación en DELETE implementada
- [x] Backend: Campo has_superadmin en response
- [x] Frontend: Lógica condicional para botones
- [x] Frontend: Texto "Cuenta del sistema" se muestra
- [x] Versión JS actualizada (v=1783264412)
- [x] Archivos copiados a producción web
- [x] uvicorn reiniciado
- [x] Testing manual: Intento de eliminar bloqueado
- [x] Testing manual: UI muestra texto correcto

---

**Implementado**: 2026-07-05
**Versión**: v1.1.1
**Estado**: ✅ En producción
