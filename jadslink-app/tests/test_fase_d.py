"""Test de FASE D: signup público, plan self-service, onboarding wizard."""


def test_fase_d(client):
    # ── 1. Registro público (sin auth) → cuenta trial + token ────────────────────
    r = client.post("/api/signup", json={
        "company_name": "Rutas del Sur", "username": "sur", "password": "sur12345",
        "email": "sur@ex.com", "contact_phone": "+58412"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["role"] == "owner" and d["token"] and d["account_id"], d
    Ho = {"Authorization": f"Bearer {d['token']}"}
    print("✓ Signup público crea cuenta y devuelve token (auto-login)")

    # ── 2. Es cuenta trial de 14 días, plan trial, tope 1 router ─────────────────
    me = client.get("/api/auth/me", headers=Ho).json()
    acc = me["account"]
    assert acc["status"] == "trial" and acc["plan"] == "trial"
    assert 12 <= acc["billing"]["days_left"] <= 14, acc["billing"]
    assert acc["usage"]["max_devices"] == 1
    print(f"✓ Cuenta trial: plan={acc['plan']}, {acc['billing']['days_left']}d, tope {acc['usage']['max_devices']} router")

    # ── 3. Validaciones de signup ────────────────────────────────────────────────
    assert client.post("/api/signup", json={"company_name":"X","username":"sur","password":"abc123"}).status_code==400  # user repetido
    assert client.post("/api/signup", json={"company_name":"Y","username":"nuevo","password":"123"}).status_code==400   # pass corta
    assert client.post("/api/signup", json={"company_name":"Z","username":"ab","password":"abc123"}).status_code==400   # user corto
    print("✓ Validaciones: usuario repetido / pass corta / usuario corto → 400")

    # ── 4. Tope del trial: 1 router ok, 2º → 403 ──────────────────────────────────
    assert client.post("/api/devices/register", headers=Ho, json={"name":"Bus 1"}).status_code==200
    assert client.post("/api/devices/register", headers=Ho, json={"name":"Bus 2"}).status_code==403
    print("✓ Trial permite 1 router; el 2º → 403")

    # ── 5. Onboarding wizard: agent.conf con credenciales ────────────────────────
    dev = client.get("/api/devices", headers=Ho).json()[0]["id"]
    ob = client.get(f"/api/devices/{dev}/onboarding", headers=Ho).json()
    assert dev in ob["agent_conf"] and ob["api_key"] in ob["agent_conf"]
    assert 'CLOUD_URL="https://link.jadsstudio.com"' in ob["agent_conf"]
    assert len(ob["steps"]) >= 3
    print("✓ Onboarding entrega agent.conf (device_id+api_key+cloud_url) y pasos")

    # ── 6. Plan self-service: owner sube a Pro → tope 20 ─────────────────────────
    r = client.patch(f"/api/accounts/{d['account_id']}", headers=Ho, json={"plan": "pro"})
    assert r.status_code == 200 and r.json()["plan"] == "pro", r.text
    me = client.get("/api/auth/me", headers=Ho).json()
    assert me["account"]["usage"]["max_devices"] == 20
    # ahora sí puede registrar el 2º router
    assert client.post("/api/devices/register", headers=Ho, json={"name":"Bus 2"}).status_code==200
    print("✓ Owner cambia su plan a Pro (self-service) → tope 20, registra 2º router")

    # ── 7. Owner NO puede cambiar el estado ni poner plan inválido ───────────────
    client.patch(f"/api/accounts/{d['account_id']}", headers=Ho, json={"status": "active"})
    # status ignorado para owner: sigue en trial
    assert client.get("/api/auth/me", headers=Ho).json()["account"]["status"] == "trial"
    assert client.patch(f"/api/accounts/{d['account_id']}", headers=Ho, json={"plan":"inexistente"}).status_code==400
    print("✓ Owner no cambia estado (ignorado) y plan inválido → 400")

    # ── 8. Aislamiento entre cuentas de signup ───────────────────────────────────
    d2 = client.post("/api/signup", json={"company_name":"Otra","username":"otra","password":"otra1234"}).json()
    Ho2 = {"Authorization": f"Bearer {d2['token']}"}
    assert len(client.get("/api/devices", headers=Ho2).json()) == 0
    assert client.get(f"/api/devices/{dev}/onboarding", headers=Ho2).status_code == 404
    print("✓ Aislamiento: cuenta nueva no ve routers ajenos ni su onboarding (404)")

    # ── 9. El superadmin ve las cuentas creadas por signup ───────────────────────
    T = client.post("/api/auth/login", json={"username":"admin","password":"admin123"}).json()["token"]
    accts = client.get("/api/accounts", headers={"Authorization": f"Bearer {T}"}).json()
    names = {a["name"] for a in accts}
    assert {"Rutas del Sur","Otra"} <= names, names
    print(f"✓ Superadmin ve {len(accts)} cuentas (incluye las de signup)")

    print("\n🎉 TODOS LOS TESTS DE FASE D PASARON")
