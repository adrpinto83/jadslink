"""Tests de la venta online de códigos: productos, tienda pública, pedidos,
aprobación con entrega automática, aislamiento y gates."""


def _login(client, u, p):
    return {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': u, 'password': p}).json()['token']}"}


def _setup(client):
    """Cuenta pro + owner + router + producto + datos de cobro. Devuelve contexto."""
    H = _login(client, "admin", "admin123")
    acc = client.post("/api/accounts", headers=H, json={
        "name": "Ventas Co", "plan": "pro", "owner_username": "vc", "owner_password": "vc123456"}).json()
    Ho = _login(client, "vc", "vc123456")
    r = client.post("/api/devices/register", headers=Ho, json={"name": "Bus Ventas"}).json()
    dev, dev_key = r["device_id"], r["api_key"]

    # datos de cobro (owner)
    r = client.patch(f"/api/accounts/{acc['id']}", headers=Ho, json={
        "payment_methods": {"pago_movil": "0412-1234567 CI 12345678 Banco X", "zelle": "op@x.com",
                            "metodo_falso": "ignorado"}})
    assert r.status_code == 200
    assert set(r.json()["payment_methods"].keys()) == {"pago_movil", "zelle"}, "solo métodos válidos"

    # producto
    p = client.post("/api/products", headers=Ho, json={
        "name": "1 Hora", "duration_min": 60, "price_usd": 1.5, "price_ves": 60.0})
    assert p.status_code == 200, p.text
    return {"H": H, "Ho": Ho, "acc": acc["id"], "dev": dev, "dev_key": dev_key, "prod": p.json()["id"]}


def test_tienda_publica_y_compra_completa(client):
    ctx = _setup(client)
    dev, prod = ctx["dev"], ctx["prod"]

    # ── Tienda pública visible sin auth ──────────────────────────────────────
    shop = client.get(f"/api/shop/{dev}").json()
    assert shop["enabled"] is True
    assert shop["products"][0]["name"] == "1 Hora" and shop["products"][0]["price_usd"] == 1.5
    assert "pago_movil" in shop["payment_methods"]
    print("✓ Tienda pública: productos y datos de cobro visibles sin auth")

    # página HTML de compra
    page = client.get(f"/buy/{dev}")
    assert page.status_code == 200 and "Comprar acceso WiFi" in page.text and dev in page.text
    print("✓ Página /buy/{device} renderiza con el device embebido")

    # el splash del portal cautivo ahora incluye el link de compra
    splash = client.get(f"/api/devices/{dev}/portal/splash").text
    assert f"/buy/{dev}" in splash
    print("✓ Splash del portal incluye el link de compra automáticamente")

    # ── Compra: crear pedido ──────────────────────────────────────────────────
    r = client.post(f"/api/shop/{dev}/orders", json={
        "product_id": prod, "method": "pago_movil", "reference": "REF777",
        "buyer_phone": "0414-5556677"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    assert client.get(f"/api/shop/orders/{token}").json()["status"] == "pending"
    print("✓ Pedido creado (pending) con token público")

    # referencia obligatoria (excepto efectivo) y producto/método inválidos
    assert client.post(f"/api/shop/{dev}/orders", json={
        "product_id": prod, "method": "pago_movil", "reference": "x"}).status_code == 400
    assert client.post(f"/api/shop/{dev}/orders", json={
        "product_id": 9999, "method": "pago_movil", "reference": "REF1234"}).status_code == 400
    assert client.post(f"/api/shop/{dev}/orders", json={
        "product_id": prod, "method": "usdt", "reference": "REF1234"}).status_code == 400  # no configurado
    print("✓ Validaciones: referencia corta / producto inválido / método no configurado → 400")

    # ── Operador aprueba → código generado y entregado ───────────────────────
    orders = client.get("/api/orders?status=pending", headers=ctx["Ho"]).json()
    oid = next(o["id"] for o in orders if o["token"] == token)
    r = client.post(f"/api/orders/{oid}/approve", headers=ctx["Ho"])
    assert r.status_code == 200 and r.json()["code"], r.text
    code = r.json()["code"]
    print(f"✓ Aprobación genera el código ({code})")

    # el comprador lo ve por su token
    st = client.get(f"/api/shop/orders/{token}").json()
    assert st["status"] == "approved" and st["code"] == code
    print("✓ El comprador ve su código en la página de estado")

    # el router lo recibe por heartbeat (Command add_codes) y lo puede validar
    hb = client.post(f"/api/devices/{dev}/heartbeat",
                     headers={"X-Api-Key": ctx["dev_key"]}, json={"clients": []}).json()
    add = [c for c in hb["commands"] if c["action"] == "add_codes" and code in c["payload"]["codes"]]
    assert add, f"add_codes no llegó al router: {hb}"
    v = client.post(f"/api/devices/{dev}/codes/validate",
                    headers={"X-Api-Key": ctx["dev_key"]}, json={"code": code, "mac": "aa:bb:cc"}).json()
    assert v["valid"] is True and v["duration"] == 3600
    print("✓ El router recibe add_codes y el código valida (3600s)")

    # re-aprobar → 400
    assert client.post(f"/api/orders/{oid}/approve", headers=ctx["Ho"]).status_code == 400
    print("✓ Re-aprobar el mismo pedido → 400")


def test_rechazo_y_aislamiento(client):
    ctx = _setup(client)
    dev, prod = ctx["dev"], ctx["prod"]

    token = client.post(f"/api/shop/{dev}/orders", json={
        "product_id": prod, "method": "zelle", "reference": "ZLL999"}).json()["token"]
    oid = client.get("/api/orders", headers=ctx["Ho"]).json()[0]["id"]

    # Otra cuenta NO ve ni puede procesar el pedido
    client.post("/api/accounts", headers=ctx["H"], json={
        "name": "Ajena", "plan": "starter", "owner_username": "aj", "owner_password": "aj123456"})
    Haj = _login(client, "aj", "aj123456")
    assert client.get("/api/orders", headers=Haj).json() == []
    assert client.post(f"/api/orders/{oid}/approve", headers=Haj).status_code == 404
    print("✓ Aislamiento: cuenta ajena no ve ni aprueba pedidos de otra")

    # Rechazo con nota → el comprador la ve
    r = client.post(f"/api/orders/{oid}/reject", headers=ctx["Ho"], json={"note": "referencia no encontrada"})
    assert r.status_code == 200
    st = client.get(f"/api/shop/orders/{token}").json()
    assert st["status"] == "rejected" and st["review_note"] == "referencia no encontrada"
    assert st["code"] == ""
    print("✓ Rechazo con nota visible para el comprador (sin código)")


def test_gates_y_roles(client):
    ctx = _setup(client)
    dev, prod = ctx["dev"], ctx["prod"]

    # viewer no gestiona productos ni pedidos, pero sí los lee
    client.post(f"/api/accounts/{ctx['acc']}/users", headers=ctx["Ho"], json={
        "username": "vw", "password": "vw123456", "role": "viewer"})
    Hv = _login(client, "vw", "vw123456")
    assert client.get("/api/orders", headers=Hv).status_code == 200
    assert client.post("/api/products", headers=Hv, json={"name": "X", "duration_min": 30, "price_usd": 1}).status_code == 403
    token = client.post(f"/api/shop/{dev}/orders", json={
        "product_id": prod, "method": "zelle", "reference": "REF55555"}).json()["token"]
    oid = client.get("/api/orders", headers=ctx["Ho"]).json()[0]["id"]
    assert client.post(f"/api/orders/{oid}/approve", headers=Hv).status_code == 403
    print("✓ Viewer: lee pedidos pero no crea productos ni aprueba (403)")

    # cuenta suspendida → tienda cerrada, no acepta pedidos ni aprobaciones
    client.patch(f"/api/accounts/{ctx['acc']}", headers=ctx["H"], json={"status": "suspended"})
    assert client.get(f"/api/shop/{dev}").json()["enabled"] is False
    assert client.post(f"/api/shop/{dev}/orders", json={
        "product_id": prod, "method": "zelle", "reference": "REF66666"}).status_code == 403
    assert client.post(f"/api/orders/{oid}/approve", headers=ctx["Ho"]).status_code == 403
    # y el splash deja de mostrar el link de compra
    assert f"/buy/{dev}" not in client.get(f"/api/devices/{dev}/portal/splash").text
    print("✓ Cuenta suspendida: tienda cerrada, sin pedidos/aprobaciones, splash sin link")

    # sin productos activos → tienda deshabilitada
    client.patch(f"/api/accounts/{ctx['acc']}", headers=ctx["H"], json={"status": "active"})
    client.delete(f"/api/products/{prod}", headers=ctx["Ho"])
    assert client.get(f"/api/shop/{dev}").json()["enabled"] is False
    print("✓ Sin productos activos → tienda deshabilitada")


def test_rate_limit_pedidos(client):
    ctx = _setup(client)
    dev, prod = ctx["dev"], ctx["prod"]
    # 6 pedidos/hora por IP; el 7º → 429
    for i in range(6):
        r = client.post(f"/api/shop/{dev}/orders", json={
            "product_id": prod, "method": "zelle", "reference": f"REF{i}0000"})
        assert r.status_code == 200, r.text
    assert client.post(f"/api/shop/{dev}/orders", json={
        "product_id": prod, "method": "zelle", "reference": "REFX0000"}).status_code == 429
    print("✓ Rate limit: 6 pedidos/hora por IP, el 7º → 429")
