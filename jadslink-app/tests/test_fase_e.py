"""Test de FASE E: enforcement de roles (RBAC) y panel de ingresos (MRR)."""
import os, tempfile, sys

DB = os.path.join(tempfile.mkdtemp(), "fe.db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
os.environ["ADMIN_PASSWORD"] = "admin123"

sys.path.insert(0, "/home/adrpinto/jadslink/jadslink-app")
from fastapi.testclient import TestClient
from api.main import app

with TestClient(app) as client:
    T = client.post("/api/auth/login", json={"username":"admin","password":"admin123"}).json()["token"]
    H = {"Authorization": f"Bearer {T}"}

    # Cuenta Pro + owner
    acc = client.post("/api/accounts", headers=H, json={
        "name":"Flota RBAC","plan":"pro","owner_username":"own","owner_password":"own12345"}).json()
    acc_id = acc["id"]
    Ho = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username':'own','password':'own12345'}).json()['token']}"}

    # Owner crea un manager y un viewer
    assert client.post(f"/api/accounts/{acc_id}/users", headers=Ho, json={
        "username":"mgr","password":"mgr12345","role":"manager"}).status_code==200
    assert client.post(f"/api/accounts/{acc_id}/users", headers=Ho, json={
        "username":"vwr","password":"vwr12345","role":"viewer"}).status_code==200
    Hm = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username':'mgr','password':'mgr12345'}).json()['token']}"}
    Hv = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username':'vwr','password':'vwr12345'}).json()['token']}"}
    print("✓ Owner crea usuarios manager y viewer")

    # Owner registra un router
    dev = client.post("/api/devices/register", headers=Ho, json={"name":"R1"}).json()["device_id"]

    # ── VIEWER: solo lectura ─────────────────────────────────────────────────────
    assert client.get("/api/devices", headers=Hv).status_code==200          # lee
    assert client.get(f"/api/devices/{dev}/codes", headers=Hv).status_code==200
    assert client.post("/api/devices/register", headers=Hv, json={"name":"X"}).status_code==403  # no registra
    assert client.post(f"/api/devices/{dev}/codes", headers=Hv, json={"quantity":1}).status_code==403  # no genera
    assert client.post(f"/api/devices/{dev}/reboot", headers=Hv).status_code==403
    assert client.post(f"/api/devices/{dev}/ssid", headers=Hv, json={"ssid":"X"}).status_code==403
    assert client.delete(f"/api/devices/{dev}", headers=Hv).status_code==403
    print("✓ Viewer: lee todo, pero registrar/generar/reboot/ssid/borrar → 403")

    # ── MANAGER: gestiona routers/códigos, pero no facturación/cuenta/usuarios ───
    assert client.post("/api/devices/register", headers=Hm, json={"name":"R2"}).status_code==200  # registra
    assert client.post(f"/api/devices/{dev}/codes", headers=Hm, json={"quantity":2}).status_code==200  # genera
    assert client.post("/api/groups", headers=Hm, json={"name":"Grupo A"}).status_code==200  # grupos
    print("✓ Manager: registra routers, genera códigos y crea grupos")

    # manager NO cambia plan/cuenta, NO crea usuarios, NO reporta pagos
    assert client.patch(f"/api/accounts/{acc_id}", headers=Hm, json={"plan":"business"}).status_code==403
    assert client.post(f"/api/accounts/{acc_id}/users", headers=Hm, json={"username":"z","password":"z12345"}).status_code==403
    assert client.post(f"/api/accounts/{acc_id}/payments", headers=Hm,
                      data={"amount_usd":"10","method":"zelle"}).status_code==403
    print("✓ Manager: cambiar plan/crear usuarios/reportar pago → 403")

    # viewer tampoco crea grupos
    assert client.post("/api/groups", headers=Hv, json={"name":"G"}).status_code==403
    print("✓ Viewer: crear grupo → 403")

    # ── OWNER: sí puede facturación y plan ───────────────────────────────────────
    assert client.patch(f"/api/accounts/{acc_id}", headers=Ho, json={"plan":"business"}).status_code==200
    assert client.post(f"/api/accounts/{acc_id}/payments", headers=Ho,
                      data={"amount_usd":"79","method":"pago_movil","reference":"R"}).status_code==200
    print("✓ Owner: cambia plan y reporta pago (OK)")

    # ── Panel de ingresos (superadmin) ───────────────────────────────────────────
    rev = client.get("/api/admin/revenue", headers=H).json()
    assert "mrr" in rev and rev["accounts_total"] >= 2 and "by_status" in rev
    assert rev["pending_payments"] >= 1  # el pago del owner está pendiente
    print(f"✓ Ingresos superadmin: MRR=${rev['mrr']}, cuentas={rev['accounts_total']}, pendientes={rev['pending_payments']}")

    # operador NO accede al panel de ingresos
    assert client.get("/api/admin/revenue", headers=Ho).status_code==403
    print("✓ Operador no accede a /api/admin/revenue (403)")

print("\n🎉 TODOS LOS TESTS DE FASE E PASARON")
