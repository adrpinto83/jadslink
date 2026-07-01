"""Test de FASE B: catálogo de planes, uso híbrido, tope max_devices y gates de estado."""
import os, tempfile, sys

DB = os.path.join(tempfile.mkdtemp(), "fb.db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
os.environ["ADMIN_PASSWORD"] = "admin123"

sys.path.insert(0, "/home/adrpinto/jadslink/jadslink-app")
from fastapi.testclient import TestClient
from api.main import app

with TestClient(app) as client:
    T = client.post("/api/auth/login", json={"username":"admin","password":"admin123"}).json()["token"]
    H = {"Authorization": f"Bearer {T}"}

    # ── 1. Catálogo de planes ────────────────────────────────────────────────────
    plans = client.get("/api/plans", headers=H).json()
    keys = {p["key"] for p in plans}
    assert keys == {"trial","starter","pro","business"}, keys
    starter = next(p for p in plans if p["key"]=="starter")
    assert starter["included_devices"]==2 and starter["max_devices"]==5 and starter["base_price_usd"]==15.0
    biz = next(p for p in plans if p["key"]=="business")
    assert biz["max_devices"] is None, "business debe ser ilimitado"
    print("✓ 4 planes seedeados; starter(2 incl/5 max/$15), business(ilimitado)")

    # ── 2. Crear cuenta Starter + login owner ────────────────────────────────────
    r = client.post("/api/accounts", headers=H, json={
        "name":"Bus Starter","plan":"starter","owner_username":"bs","owner_password":"bs123456"})
    assert r.status_code==200, r.text
    acc_id = r.json()["id"]
    To = client.post("/api/auth/login", json={"username":"bs","password":"bs123456"}).json()["token"]
    Ho = {"Authorization": f"Bearer {To}"}
    print("✓ Cuenta Starter creada + login owner")

    # ── 3. Uso inicial (0 routers): base $15, sin extras ─────────────────────────
    me = client.get("/api/auth/me", headers=Ho).json()
    u = me["account"]["usage"]
    assert u["plan"]=="starter" and u["device_count"]==0 and u["included_devices"]==2
    assert u["max_devices"]==5 and u["total_monthly"]==15.0 and u["extra_devices"]==0
    print(f"✓ Uso inicial: {u['device_count']}/{u['included_devices']} incl, total ${u['total_monthly']}")

    # ── 4. Cobro híbrido: 3 routers → 1 extra → $15 + $6 = $21 ────────────────────
    for i in range(3):
        assert client.post("/api/devices/register", headers=Ho,
                           json={"name":f"Bus {i+1}"}).status_code==200
    u = client.get("/api/auth/me", headers=Ho).json()["account"]["usage"]
    assert u["device_count"]==3 and u["extra_devices"]==1 and u["extra_cost"]==6.0 and u["total_monthly"]==21.0, u
    print(f"✓ 3 routers → 1 extra × $6 = ${u['extra_cost']}; total ${u['total_monthly']}")

    # ── 5. Tope del plan: registrar hasta 5 ok, el 6º → 403 ──────────────────────
    for i in range(2):  # llegar a 5
        assert client.post("/api/devices/register", headers=Ho, json={"name":f"Bus {i+4}"}).status_code==200
    r = client.post("/api/devices/register", headers=Ho, json={"name":"Bus 6"})
    assert r.status_code==403 and "límite" in r.json()["detail"].lower(), r.text
    print("✓ Tope max_devices=5 respetado; el 6º router → 403")

    # superadmin SÍ puede exceder el tope (gestiona el cobro manualmente)
    assert client.post("/api/devices/register", headers=H,
                       json={"name":"Bus extra superadmin","account_id":acc_id}).status_code==200
    print("✓ Superadmin puede exceder el tope (6 routers en la cuenta)")

    # ── 6. Preparar un código para probar el gate de validación ──────────────────
    dev = client.get("/api/devices", headers=Ho).json()[0]["id"]
    assert client.post(f"/api/devices/{dev}/codes", headers=Ho,
                      json={"quantity":1,"duration_min":60}).status_code==200
    code = client.get(f"/api/devices/{dev}/codes", headers=Ho).json()[0]["code"]
    # validación normal (cuenta activa) → válido
    r = client.post(f"/api/devices/{dev}/codes/validate", json={"code":code,"mac":"aa:bb"})
    assert r.json()["valid"] is True, r.text
    print("✓ Código válido con cuenta activa")

    # ── 7. Suspensión: superadmin suspende la cuenta ─────────────────────────────
    r = client.patch(f"/api/accounts/{acc_id}", headers=H, json={"status":"suspended"})
    assert r.status_code==200 and r.json()["status"]=="suspended", r.text

    # owner NO puede generar códigos
    r = client.post(f"/api/devices/{dev}/codes", headers=Ho, json={"quantity":1})
    assert r.status_code==403 and "suspendida" in r.json()["detail"].lower(), r.text
    print("✓ Cuenta suspendida: generar códigos → 403")

    # owner NO puede registrar routers
    assert client.post("/api/devices/register", headers=Ho, json={"name":"x"}).status_code==403
    print("✓ Cuenta suspendida: registrar router → 403")

    # validación (agente) rechaza por cuenta suspendida
    code2 = client.get(f"/api/devices/{dev}/codes", headers=Ho)  # aún puede leer
    r = client.post(f"/api/devices/{dev}/codes/validate", json={"code":code,"mac":"cc:dd"})
    assert r.json()["valid"] is False and r.json()["reason"]=="account_suspended", r.text
    print("✓ Cuenta suspendida: /validate del agente → account_suspended")

    # ── 8. Reactivación ──────────────────────────────────────────────────────────
    client.patch(f"/api/accounts/{acc_id}", headers=H, json={"status":"active"})
    r = client.post(f"/api/devices/{dev}/codes", headers=Ho, json={"quantity":1})
    assert r.status_code==200, r.text
    print("✓ Reactivada: vuelve a generar códigos")

print("\n🎉 TODOS LOS TESTS DE FASE B PASARON")
