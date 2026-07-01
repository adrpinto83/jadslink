# JADSlink — Plan de conversión a SaaS por suscripción

**Objetivo**: convertir la base funcional single-tenant actual en una plataforma multi-tenant
donde cada operador gestiona sus routers (o grupos de routers), y paga una suscripción mensual.

**Decisiones de negocio fijadas (2026-06-30)**
- **Cobro híbrido**: plan base incluye N routers + $X/mes por router adicional.
- **Pago local Venezuela** (Pago móvil, transferencia, Zelle, USDT) con reporte de comprobante + aprobación manual.
- **Activación manual**: el superadmin activa/suspende/extiende la vigencia de cada cuenta.
- Stripe **descartado** (no recibe pagos en Venezuela).

---

## 1. Punto de partida (base funcional actual)

`jadslink-app` hoy es single-tenant:
- `Device` (routers) — **sin dueño**, `api_key`, config, heartbeat, comandos.
- `Client`, `Code`, `Report`, `Command` — todos colgados de `device_id`.
- `AdminUser` — **un solo admin** (username/password, sin roles ni cuenta).
- `Settings` — key/value global.
- Auth: token HMAC firmado `{u: username}` (stateless, 30d) → `require_admin`.

Todo funciona (portal cautivo, códigos, expiración, agente OpenWrt, deploy). Falta la capa de
**propiedad, aislamiento, planes y cobro**.

---

## 2. Modelo de datos objetivo

### Tablas nuevas

**Account** (el operador que paga — el tenant)
| campo | tipo | nota |
|---|---|---|
| id | UUID | |
| name | str | "Transportes ABC" |
| slug | str unique | url-safe |
| status | str | `trial` / `active` / `past_due` / `suspended` / `canceled` |
| plan_id | FK SubscriptionPlan | plan contratado |
| billing_cycle_end | datetime | hasta cuándo está pagado |
| trial_ends_at | datetime\|null | fin del trial |
| created_at, updated_at | | |

**User** (reemplaza y extiende `AdminUser`)
| campo | tipo | nota |
|---|---|---|
| id | int/UUID | |
| account_id | FK Account\|null | null = superadmin (JADS) |
| email | str unique | login |
| password_hash | str | |
| full_name | str | |
| role | str | `superadmin` / `owner` / `manager` / `viewer` |
| is_active | bool | |

Roles dentro de una cuenta: **owner** (todo + pagos), **manager** (routers/códigos, sin pagos),
**viewer** (solo lectura/reportes).

**SubscriptionPlan** (catálogo)
| campo | nota |
|---|---|
| id, name | Starter / Pro / Business |
| base_price_usd | precio base mensual |
| included_devices | routers incluidos en la base |
| price_per_extra_device_usd | costo por router adicional |
| max_devices | tope duro (null = ilimitado) |
| features (JSON) | `reports_advanced`, `api_access`, `whitelabel`, ... |
| is_active | |

**DeviceGroup** (agrupar routers: por ruta, flota, zona)
| campo | nota |
|---|---|
| id, account_id (FK), name, created_at | |

**Payment** (reporte de pago semi-manual)
| campo | nota |
|---|---|
| id, account_id (FK) | |
| amount_usd | monto reportado |
| method | `pago_movil` / `transferencia` / `zelle` / `usdt` / `efectivo` |
| reference | nro. de referencia / hash tx |
| proof_url | comprobante subido (opcional) |
| period_start, period_end | mes que cubre |
| status | `pending` / `approved` / `rejected` |
| reviewed_by (FK User) | superadmin que aprobó |
| created_at, reviewed_at, note | |

**BillingRecord** (factura/estado de cuenta por periodo)
| campo | nota |
|---|---|
| id, account_id (FK) | |
| period_start, period_end | |
| device_count | routers activos ese periodo |
| base_amount, extra_amount, total_amount | cálculo híbrido |
| status | `due` / `paid` / `overdue` |
| payment_id (FK Payment\|null) | |

### Tablas modificadas
- **Device**: `+ account_id (FK Account)`, `+ group_id (FK DeviceGroup, null)`.
- Backfill: todos los devices actuales → una cuenta "JADS Studio" (superadmin) al migrar.

### Aislamiento multi-tenant
- Toda query de `Device/Client/Code/Report/Command` filtra por `account_id`.
- Dependencia `require_account(user)` resuelve la cuenta del token; **superadmin ve todo**.
- Token HMAC pasa a `{uid, account_id, role}` (extensión del actual, sigue stateless).

---

## 3. Lógica de suscripción y cobro (manual + pagos locales)

**Cálculo del monto (híbrido)**
```
total = base_price + max(0, routers_activos - included_devices) * price_per_extra_device
```

**Ciclo mensual**
1. `billing_cycle_end` marca hasta cuándo está pagada la cuenta.
2. Cron diario (APScheduler, ya usado en el proyecto) genera `BillingRecord` del periodo y calcula el total.
3. Operador reporta pago → crea `Payment` (`pending`) con método, referencia y comprobante.
4. Superadmin revisa en el panel → **aprueba** → `billing_cycle_end += 30d`, cuenta `active`, BillingRecord `paid`.
5. Si `billing_cycle_end < hoy` → `past_due` (periodo de gracia ~5 días) → luego `suspended`.

**Efecto de suspensión**
- No se pueden generar códigos nuevos.
- Heartbeat del agente recibe flag `suspended` → el portal muestra "servicio suspendido" (o rechaza validaciones).
- Superadmin puede reactivar/extender manualmente en cualquier momento.

**Enforcement de límites**
- Registrar router: si `routers_activos >= max_devices` → bloquear (o cobrar extra según plan).
- Dashboard muestra uso: "routers usados / incluidos (+N extra = $Y)".

---

## 4. Planes propuestos (borrador, ajustable)

| Plan | Base/mes | Routers incluidos | Router extra | Tope | Features |
|---|---|---|---|---|---|
| **Starter** | $15 | 2 | $6/mes | 5 | dashboard, códigos, portal branding |
| **Pro** | $29 | 5 | $5/mes | 20 | + reportes avanzados, grupos, multi-usuario |
| **Business** | $79 | 15 | $4/mes | ∞ | + white-label, API, soporte prioritario |
| **Trial** | $0 | 1 | — | 1 | 14 días, full features |

---

## 5. Plan de implementación por fases

### FASE A — Fundación multi-tenant (sin cobro todavía)
- Modelos `Account`, `User` (migrar `AdminUser`), `Device.account_id`, `DeviceGroup`.
- Migración Alembic + backfill de devices existentes a cuenta "JADS Studio".
- Auth: token con `account_id + role`; `require_account`; scope de todas las queries.
- `superadmin` = admin actual. Panel: cambio de contexto de cuenta.
- Dashboard: UI de grupos de routers.
- **Entregable**: cada usuario ve solo sus routers; superadmin ve todo.

### FASE B — Planes y límites
- Catálogo `SubscriptionPlan` + seed. Asignar plan a cuenta.
- Enforce `max_devices`; indicador de uso (incluidos + extras) en dashboard.
- Gates de estado: cuenta `suspended` bloquea generación de códigos y portal.

### FASE C — Pagos locales + facturación
- `Payment` (con upload de comprobante) + `BillingRecord` + cálculo híbrido.
- Flujo de aprobación en panel superadmin (aprobar/rechazar → extiende ciclo).
- APScheduler: `due` / `past_due` / `suspended` con gracia; notificaciones (email / link WhatsApp).
- **Entregable**: cobro operativo end-to-end sin pasarela automática.

### FASE D — Self-service + onboarding
- Registro público → cuenta `trial` (14 días) automática.
- Wizard de alta de router (registrar device, entregar `api_key`, script de instalación).
- Conversión trial → pago.

### FASE E — Escala y pulido
- Roles granulares + audit log.
- White-label por cuenta (branding del portal ya existe parcialmente).
- Reportes de ingresos por cuenta, exportación, API pública.
- Multi-router bulk ops (comandos a grupos completos).

---

## 6. Riesgos / notas técnicas
- **Migración de datos**: los devices y códigos actuales deben quedar bajo una cuenta al migrar (no perder el router en campo `e4916825-...`).
- **Aislamiento estricto**: cada endpoint debe filtrar por `account_id`; tests de aislamiento obligatorios.
- **El agente OpenWrt no cambia** en FASE A–B: sigue autenticando por `api_key` del device; solo el backend sabe a qué cuenta pertenece.
- **Suspensión en campo**: definir si el router deja de servir al suspender (recomendado: el portal `/validate` del cloud responde inválido + splash "suspendido"), respetando operación offline del agente.
