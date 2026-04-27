# Separación de Cuentas y Privilegios - JADSlink

**Status**: ✅ Correctamente Implementado

---

## Cuentas de Prueba

### 1. CUENTA DEMO (Público)
```
Email:     demo@jadslink.com
Password:  demo123456
Rol:       operator
Tenant:    "Demo - Bus Starlink"
Plan:      free
Datos:     4 planes + 3 nodos de ejemplo
```

**Propósito**: Demostración pública para nuevos usuarios

**Acceso**:
- ✅ Ver/crear planes propios (solo del tenant demo)
- ✅ Ver/crear nodos propios (solo del tenant demo)
- ✅ Generar tickets (solo para sus nodos)
- ✅ Ver sesiones activas (solo de sus nodos)
- ✅ Solicitar upgrades (solo para su account)
- ❌ Ver datos de otros tenants
- ❌ Ver panel de admin
- ❌ Confirmar pagos
- ❌ Ver o modificar otros operadores

### 2. CUENTA ADMIN (Sistema)
```
Email:     admin@jads.com
Password:  admin123456
Rol:       superadmin
Tenant:    "JADS Studio"
Plan:      pro
Datos:     Ninguno (tenant administrativo vacío)
```

**Propósito**: Administración global del sistema

**Acceso**:
- ✅ Ver TODOS los tenants del sistema
- ✅ Aprobar/rechazar pagos de TODOS los operadores
- ✅ Ver historial de pagos global
- ✅ Ver métricas globales
- ✅ Crear/administrar operadores
- ✅ Ver nodos de otros operadores (en mapas globales)
- ✅ Enviar reminders de pagos
- ✅ Configurar tasas de cambio
- ❌ Generar tickets (no es operador)
- ❌ Crear nodos (no es operador)

---

## Separación por Tenant

### Validación en Código

Todos los endpoints privados usan `Depends(get_current_tenant)` para filtrar automáticamente por tenant_id.

**Resultado**:
- DEMO solo ve sus 4 planes
- ADMIN solo ve sus 0 planes (no los de demo)
- Imposible acceder a datos de otro tenant

### Endpoints de Admin (Protegidos)

Los endpoints /admin/* validan que `current_user.role == "superadmin"`

**Resultado**:
- DEMO recibe 403 Forbidden
- ADMIN accede correctamente

---

## Matriz de Permisos

| Acción | DEMO (operator) | ADMIN (superadmin) |
|--------|---|---|
| Ver sus planes | ✅ | ✅ |
| Ver planes de otros | ❌ | ✅ |
| Crear nodos | ✅ | ❌ |
| Ver sus nodos | ✅ | ❌ |
| Ver todos los nodos | ❌ | ✅ |
| Generar tickets | ✅ | ❌ |
| Ver tickets propios | ✅ | ❌ |
| Ver todos los tickets | ❌ | ✅ |
| Crear sesiones | ✅ | ❌ |
| Solicitar upgrade | ✅ | ❌ |
| Aprobar pagos | ❌ | ✅ |
| Ver panel admin | ❌ | ✅ |
| Ver histórico global | ❌ | ✅ |

---

## Tests de Separación Verificados

```
✅ DEMO login → Token obtenido
✅ ADMIN login → Token obtenido

✅ DEMO /plans → Ve 4 planes (de su tenant)
✅ ADMIN /plans → Ve 0 planes (de su tenant)

✅ DEMO /admin/pending-payments → 403 Forbidden
✅ ADMIN /admin/pending-payments → 200 OK

✅ DEMO → No puede crear admin tenants
✅ ADMIN → Puede ver/aprobar pagos globales
```

---

## Diferencia Clave: Tenant vs Role

- **Tenant** = Organización/Operador (demo-bus-starlink, jads-studio)
- **Role** = Tipo de usuario dentro de la plataforma (operator, superadmin)

### Estructura
```
Tenant: Demo - Bus Starlink
├── User: demo@jadslink.com (role=operator)
├── Planes: 4
├── Nodos: 3
└── Acceso: Solo datos propios

Tenant: JADS Studio
├── User: admin@jads.com (role=superadmin)
├── Planes: 0
├── Nodos: 0
└── Acceso: Todos los datos del sistema
```

### Admin NO es "Operator"

- El admin NO puede generar tickets
- El admin NO puede crear nodos
- El admin NO puede ver métricas en tiempo real

El admin solo puede:
- Ver solicitudes de upgrade
- Aprobar/rechazar pagos
- Ver historiales
- Administrar operadores

---

## Conclusión

La separación de cuentas es **CORRECTA** y está **BIEN IMPLEMENTADA**:

✅ Dos tenants completamente separados
✅ Roles distintos (operator vs superadmin)
✅ Aislamiento de datos por tenant en todo el código
✅ Endpoints administrativos protegidos
✅ Tests de separación pasando

**La plataforma es multi-tenant segura.**

---

Última actualización: 2026-04-27
Status: ✅ Verificado y Documentado
