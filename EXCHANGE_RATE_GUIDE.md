# Guía de Actualización de Tasa de Cambio BCV

## 📊 Tasa Actual

Para ver la tasa actual del sistema:

```bash
curl http://localhost:8000/api/v1/utils/exchange-rate
```

Respuesta:
```json
{
    "rate": 37.5,
    "source": "manual",
    "updated_at": "2026-04-26T19:26:02.416079+00:00"
}
```

---

## 🔄 Métodos para Actualizar la Tasa

### Método 1: SQL Directo (Más Rápido)

Ejecutar desde la BD:

```bash
docker compose exec -T db psql -U jads -d jadslink << 'EOF'
-- Desactivar todas las tasas previas
UPDATE exchange_rates SET is_active = false;

-- Insertar nueva tasa
INSERT INTO exchange_rates (id, rate, source, is_active, updated_by, notes, created_at, updated_at)
VALUES (gen_random_uuid(), 38.50, 'manual', true, 'system', 'Tasa oficial BCV actualizada', now(), now());

-- Verificar
SELECT rate, source, is_active, created_at FROM exchange_rates WHERE is_active = true LIMIT 1;
EOF
```

### Método 2: Endpoint Admin (Futuro)

```bash
# 1. Obtener token de superadmin
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@jads.com", "password": "admin123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Actualizar tasa
curl -X POST http://localhost:8000/api/v1/utils/exchange-rate/admin-update \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"rate": 38.50, "notes": "Tasa oficial BCV"}'
```

---

## 📱 Verificar en Frontend

1. Abrir en browser: `http://localhost:5173`
2. Ir a **Facturación y Planes** (tab: "Comprar o Actualizar")
3. Seleccionar un plan
4. La **tasa en VEF** debe mostrar el valor actualizado

**Nota**: Si sigue mostrando la tasa antigua:
- Presionar `F5` o `Ctrl+Shift+R` (hard refresh)
- O abrir en incógnito para evitar caché

---

## ⏱️ Actualización Automática

El sistema tiene un **job automático** que intenta:

1. **9 AM**: Scraping de bcv.org.ve
2. **Si falla**: Fallback a exchangerate-api.com
3. **Si ambos fallan**: Mantiene la tasa actual

Para ejecutar manualmente el job:

```bash
docker compose exec api python3 << 'EOF'
import asyncio
from database import async_session_maker
from services.exchange_rate_service import ExchangeRateService

async def run():
    async with async_session_maker() as db:
        success, message = await ExchangeRateService.update_rate(db)
        await db.commit()
        print(f"✅ {message}" if success else f"❌ {message}")

asyncio.run(run())
EOF
```

---

## 📊 Historial de Tasas

Ver todas las tasas registradas:

```bash
docker compose exec -T db psql -U jads -d jadslink << 'EOF'
SELECT rate, source, is_active, updated_by, notes, created_at
FROM exchange_rates
ORDER BY created_at DESC
LIMIT 10;
EOF
```

---

## 🔧 Configuración

En `api/config.py`:
- `RESEND_API_KEY`: API key para emails (opcional)
- `EMAIL_FROM`: Email remitente
- `SUPPORT_EMAIL`: Email de soporte

En `api/.env`:
```bash
RESEND_API_KEY=re_your_key_here  # Opcional
```

---

## ✅ Checklist de Funcionamiento

- [ ] Endpoint `/api/v1/utils/exchange-rate` devuelve la tasa actual
- [ ] Frontend muestra tasa dinámicamente (refetch cada minuto)
- [ ] Formulario Pago Móvil calcula VEF según tasa
- [ ] Datos bancarios JADSlink visibles:
  - Cédula: V-16140066
  - Teléfono: 0424-8886222
  - Bancos: Bancamiga, Mercantil, Venezuela
- [ ] Upload de comprobantes funciona
- [ ] Validaciones de cédula/referencia funcionan

---

## 📞 Soporte

Si la tasa no se actualiza:

1. Verificar que la BD está corriendo: `docker compose ps`
2. Ver logs del API: `docker compose logs api | grep exchange`
3. Actualizar manualmente usando Método 1 (SQL)

