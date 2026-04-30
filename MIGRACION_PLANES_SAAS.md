# 🚀 Guía de Migración e Implementación de Planes SaaS

## Estado: LISTO PARA DEPLOY

Todos los archivos están creados y listos. Sigue estos pasos para activar los nuevos planes SaaS.

---

## FASE 1: Preparación (LOCAL O EN SERVIDOR)

### 1.1 Verificar la Base de Datos
```bash
# Asegúrate que PostgreSQL/MySQL está corriendo
# Para desarrollo local con Docker:
docker-compose up -d db

# O si tienes BD en Hostinger/servidor remoto, verifica conexión
psql -U jads -h localhost -d jadslink -c "SELECT version();"
```

### 1.2 Instalar/Actualizar Dependencias
```bash
cd /home/adrpinto/jadslink
pip install alembic sqlalchemy psycopg2-binary
```

---

## FASE 2: Ejecutar Migración Alembic

### 2.1 Aplicar la Migración a la Base de Datos
```bash
cd /home/adrpinto/jadslink/api

# Ejecutar la migración que crea tabla pricing_plans
python3 -m alembic upgrade head
```

✅ **Esperado:**
```
INFO  [alembic.runtime.migration] Context impl PostgreSQLImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.migration] Running upgrade 8f8548709ef9 -> a7c2f8d9e4b1, create_pricing_plans_table
INFO  [alembic.migration] Done.
```

### 2.2 Verificar que la Tabla se Creó
```bash
cd /home/adrpinto/jadslink/api

python3 << 'EOF'
from sqlalchemy import inspect, create_engine
from config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

inspector = inspect(engine)
columns = inspector.get_columns('pricing_plans')

print("✅ Tabla 'pricing_plans' creada con éxito!")
print(f"   Columnas: {len(columns)}")
for col in columns[:5]:
    print(f"   - {col['name']}: {col['type']}")
EOF
```

---

## FASE 3: Seed (Insertar los 4 Planes)

### 3.1 Ejecutar Script de Seed
```bash
cd /home/adrpinto/jadslink

python3 api/scripts/seed_pricing_plans.py
```

✅ **Esperado:**
```
✅ 4 planes SaaS creados exitosamente:
   • Gratuito: $0 (50 tickets/mes)
   • Básico: $29 (200 tickets/mes)
   • Estándar: $79 (1,000 tickets/mes, 3 nodos) [RECOMENDADO]
   • Pro: $199 (Ilimitado)
```

### 3.2 Verificar Datos en la BD
```bash
cd /home/adrpinto/jadslink/api

python3 << 'EOF'
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker
from models.pricing_plan import PricingPlan
from config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

plans = session.query(PricingPlan).order_by(PricingPlan.sort_order).all()
print(f"\n✅ {len(plans)} planes encontrados en BD:\n")
for plan in plans:
    print(f"  • {plan.name.upper()}")
    print(f"    - Tier: {plan.tier}")
    print(f"    - Precio: ${plan.monthly_price}/mes")
    print(f"    - Tickets: {plan.included_tickets_per_month} incluidos")
    print(f"    - Nodos: {plan.included_nodes} incluidos")
    print(f"    - Recomendado: {plan.is_recommended}")
    print()

session.close()
EOF
```

---

## FASE 4: Levantar API y Verificar Endpoint

### 4.1 Iniciar API (desde el directorio raíz)
```bash
cd /home/adrpinto/jadslink

# Opción 1: Uvicorn directo
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Opción 2: Si tienes Docker disponible
docker-compose up api
```

### 4.2 Probar Endpoint GET /api/v1/saas-plans
```bash
# En otra terminal:
curl -s http://localhost:8000/api/v1/saas-plans | python3 -m json.tool
```

✅ **Esperado:**
```json
[
  {
    "tier": "free",
    "name": "Gratuito",
    "description": "Perfecto para probar el sistema sin compromiso",
    "monthly_price": 0.0,
    "monthly_price_display": "$0",
    "included_tickets": 50,
    "is_tickets_unlimited": false,
    "included_nodes": 1,
    "is_nodes_unlimited": false,
    "features": [
      {
        "icon": "ticket",
        "text": "50 tickets/mes incluidos",
        "included": true
      },
      ...
    ],
    "is_recommended": false,
    "badge": null
  },
  ...
]
```

### 4.3 Verificar en Swagger/Docs
Abre el navegador:
```
http://localhost:8000/docs
```

Busca el endpoint `GET /api/v1/saas-plans` y pruébalo.

---

## FASE 5: Tests Unitarios (Opcional pero Recomendado)

### 5.1 Crear Test para Endpoint
```bash
cd /home/adrpinto/jadslink

python3 << 'EOF'
import asyncio
import httpx
from config import get_settings

async def test_saas_plans():
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/saas-plans",
            timeout=5.0
        )

        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200, "Endpoint debe retornar 200"

        plans = response.json()
        print(f"Planes obtenidos: {len(plans)}")
        assert len(plans) == 4, "Deben haber 4 planes"

        # Verificar plan estándar
        standard = next((p for p in plans if p['tier'] == 'standard'), None)
        assert standard is not None, "Plan estándar debe existir"
        assert standard['monthly_price'] == 79.0
        assert standard['included_nodes'] == 3
        assert standard['included_tickets'] == 1000
        assert standard['is_recommended'] == True

        print("\n✅ TODOS LOS TESTS PASARON\n")
        for plan in plans:
            print(f"  ✓ {plan['name']}: ${plan['monthly_price']}/mes")

asyncio.run(test_saas_plans())
EOF
```

### 5.2 Ejecutar Tests con Pytest (si lo tienes configurado)
```bash
cd /home/adrpinto/jadslink

# Crear test file
cat > test_saas_plans.py << 'EOF'
import pytest
from httpx import AsyncClient
from api.main import app

@pytest.mark.asyncio
async def test_get_saas_plans():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/saas-plans")
        assert response.status_code == 200

        plans = response.json()
        assert len(plans) == 4

        tiers = {p['tier'] for p in plans}
        assert tiers == {'free', 'basic', 'standard', 'pro'}

        # Verificar plan estándar
        standard = next(p for p in plans if p['tier'] == 'standard')
        assert standard['is_recommended'] == True
        assert standard['monthly_price'] == 79.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

pytest test_saas_plans.py -v
```

---

## FASE 6: Verificación en Frontend

### 6.1 Iniciar Dashboard
```bash
cd /home/adrpinto/jadslink/dashboard

npm run dev
# O si tienes Vite:
npx vite
```

### 6.2 Verificar Páginas
- **Login** (`http://localhost:5173/login`):
  - ✅ Deben verse 4 planes en grid
  - ✅ Plan "Estándar" debe tener badge "Más Popular"
  - ✅ Plan "Estándar" debe estar escalado (scale-105)

- **Billing** (`http://localhost:5173/dashboard/billing`):
  - ✅ Deben verse 4 planes dinámicos
  - ✅ Sin hardcoding de features
  - ✅ Features vienen desde el endpoint `/api/v1/saas-plans`

- **Admin Subscriptions** (`http://localhost:5173/dashboard/admin/subscriptions`):
  - ✅ Select con opción "ESTÁNDAR - 1,000 tickets/mes, 3 nodos"

---

## FASE 7: Checklist de Verificación Final

### Backend
- [ ] Migración ejecutada sin errores
- [ ] Tabla `pricing_plans` creada con 4 registros
- [ ] Endpoint GET `/api/v1/saas-plans` retorna 200
- [ ] JSON contiene 4 planes: free, basic, standard, pro
- [ ] Plan "standard" tiene `is_recommended: true`
- [ ] Plan "standard" tiene `included_nodes: 3`
- [ ] Plan "standard" tiene `included_tickets_per_month: 1000`
- [ ] Precios correctos: $0, $29, $79, $199

### Frontend
- [ ] Login muestra 4 planes
- [ ] Plan "Estándar" tiene badge "Más Popular"
- [ ] Plan "Estándar" está más grande (scale-105)
- [ ] Billing renderiza features dinámicamente
- [ ] Admin panel permite otorgar plan "standard"
- [ ] No hay referencias a "starter" o "enterprise"

### E2E
- [ ] Login → Ver 4 planes
- [ ] Registrar usuario → Asignar plan "standard"
- [ ] Dashboard → Ver plan actual
- [ ] Cambiar plan en BD → Frontend actualiza automáticamente

---

## 🆘 Solución de Problemas

### Error: "tabla pricing_plans no existe"
```bash
# Ejecutar migración nuevamente
cd api
python3 -m alembic upgrade head

# Verificar historial de migraciones
python3 -m alembic history
```

### Error: "Conexión a BD fallida"
```bash
# Verificar .env
cat .env | grep DATABASE_URL

# Verificar conexión
psql -U jads -h localhost -d jadslink -c "SELECT 1"
```

### Frontend no muestra planes
```bash
# Verificar que API está corriendo
curl http://localhost:8000/api/v1/saas-plans

# Verificar CORS en dev
# Abre DevTools → Console, busca errores 403/CORS

# Verificar cache
# En navegador: F12 → Application → Storage → Clear Site Data
```

### Test falla: "4 planes no encontrados"
```bash
# Verificar datos en BD
python3 << 'EOF'
from sqlalchemy import create_engine, text
from config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM pricing_plans"))
    count = result.scalar()
    print(f"Planes en BD: {count}")

    result = conn.execute(text("SELECT tier, name, monthly_price FROM pricing_plans ORDER BY sort_order"))
    for row in result:
        print(f"  • {row[1]}: ${row[2]}")
EOF
```

---

## 📊 Resumen de Cambios

**Backend:**
- ✅ Modelo `PricingPlan` creado
- ✅ Router `/api/v1/saas-plans` implementado
- ✅ Migración Alembic creada
- ✅ Enum `PlanTier` actualizado con "standard"
- ✅ Script seed con 4 planes

**Frontend:**
- ✅ Hook `useSaaSPlans` creado
- ✅ Tipo `SaaSPlan` definido
- ✅ Login.tsx usa datos dinámicos
- ✅ Billing.tsx usa datos dinámicos
- ✅ AdminSubscriptions.tsx incluye "standard"

---

## 🎉 ¡Listo para Producción!

Una vez completados todos estos pasos:

1. Los 4 planes estarán en la base de datos
2. El frontend obtiene planes dinámicamente
3. Cambios en BD reflejan automáticamente en UI
4. Sistema es escalable (agregar plan = 1 INSERT)

**Comando rápido para todo (si todo está configurado):**
```bash
cd /home/adrpinto/jadslink && \
python3 -m alembic upgrade head && \
python3 api/scripts/seed_pricing_plans.py && \
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

Generado: 2026-04-30
Estado: ✅ LISTO PARA DEPLOY
