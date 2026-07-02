# Deploy con el paquete de seguridad (2026-07)

Cambios de este paquete que afectan el deploy a producción (link.jadsstudio.com):

## 1. Variables de entorno nuevas / recomendadas (`.env` del servidor)

```bash
# OBLIGATORIO antes del próximo deploy: el seed del router ya NO está en el código.
# Sin esto, si la BD se recrea, el router de campo queda huérfano (heartbeat 401).
SEED_DEVICES_JSON='[{"id":"e4916825-74af-42ac-b3dc-ba26e4647e19","name":"Router Hotspot Principal","api_key":"<API_KEY_DEL_ROUTER>","location":"Lobby","model":"OpenWrt 23.05.3","firmware":"OpenWrt 23.05.3"}]'
# (alternativa: crear el archivo <DATA_DIR>/seed_devices.json con ese JSON)

# Recomendado: secreto fijo para tokens (si falta, se autogenera y persiste en DATA_DIR/jwt_secret)
JWT_SECRET=<secreto aleatorio largo>

# Recomendado: mover los datos FUERA del árbol de deploy para sobrevivir redeploys
DATA_DIR=/home/<usuario>/jadslink-data

# Opcionales (defaults sanos)
TOKEN_TTL_DAYS=7            # duración de la sesión del panel
REPORT_RETENTION_DAYS=30    # poda de métricas históricas
CLIENT_RETENTION_DAYS=90    # poda de clientes inactivos
```

## 2. Acciones manuales post-deploy (una sola vez)

1. **Cambiar la contraseña del superadmin** desde el panel (Configuración → Contraseña).
   El seed inicial usa `admin123` si `ADMIN_PASSWORD` no está definido — hoy prod está así.
2. **Rotar el api_key del router de campo**: el anterior quedó en el historial de git.
   - Generar api_key nuevo (o re-registrar el device), actualizar `/etc/hotspot/agent.conf`
     en el router y el `SEED_DEVICES_JSON` del servidor.
3. Verificar que `DATA_DIR` (o `data/`) es persistente entre deploys: ahí viven la BD
   SQLite, `jwt_secret`, `seed_devices.json` y los comprobantes (`proofs/`).

## 3. Efectos visibles del deploy

- **Todas las sesiones del panel se cierran** (formato de token nuevo): cada usuario
  vuelve a hacer login una vez. Al loguearse, su hash se migra solo a pbkdf2.
- El `/validate` del portal cautivo ahora **exige la API key del router** — el script
  `jadslink-auth.sh` desplegado ya la envía, no hay que tocar el router para esto.
- Rate limits activos: login 5 fallos/5min por usuario, signup 10/hora por IP,
  validate 10/min por MAC.
- Los roles `viewer` ya no ven los `api_key` de los routers ni el onboarding.
