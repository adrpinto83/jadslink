"""Tests del paquete de seguridad: hashing pbkdf2, rate limiting,
invalidación de tokens al cambiar contraseña y visibilidad de api_keys."""


def _login(client, username, password):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_hash_pbkdf2_y_rehash(client):
    from api.database import SessionLocal
    from api.models import User

    T = _login(client, "admin", "admin123").json()["token"]
    H = {"Authorization": f"Bearer {T}"}

    # Usuarios nuevos se guardan con pbkdf2 (con salt), nunca sha256 plano.
    client.post("/api/accounts", headers=H, json={
        "name": "Sec Co", "owner_username": "sec", "owner_password": "sec12345"})
    db = SessionLocal()
    u = db.query(User).filter(User.username == "sec").first()
    assert u.password_hash.startswith("pbkdf2$"), u.password_hash[:20]
    # El superadmin también quedó re-hasheado tras su login.
    a = db.query(User).filter(User.username == "admin").first()
    assert a.password_hash.startswith("pbkdf2$")
    db.close()
    print("✓ Hashes pbkdf2 con salt para usuarios nuevos y re-hash del admin")


def test_login_rate_limit(client):
    # 5 fallos seguidos sobre el mismo usuario → el 6º intento devuelve 429.
    for i in range(5):
        assert _login(client, "fantasma", f"mal{i}").status_code == 401
    assert _login(client, "fantasma", "mal6").status_code == 429
    # Otro usuario desde la misma IP no queda bloqueado (límite por usuario).
    assert _login(client, "admin", "admin123").status_code == 200
    print("✓ Rate limit de login: 5 fallos → 429; no afecta a otros usuarios")


def test_token_invalido_al_cambiar_password(client):
    T = _login(client, "admin", "admin123").json()["token"]
    H = {"Authorization": f"Bearer {T}"}
    client.post("/api/accounts", headers=H, json={
        "name": "Rot Co", "owner_username": "rot", "owner_password": "rot12345"})

    tok_viejo = _login(client, "rot", "rot12345").json()["token"]
    Hv = {"Authorization": f"Bearer {tok_viejo}"}
    assert client.get("/api/auth/me", headers=Hv).status_code == 200

    r = client.put("/api/auth/password", headers=Hv, json={
        "current_password": "rot12345", "new_password": "nuevaClave99"})
    assert r.status_code == 200, r.text

    # El token emitido antes del cambio queda inválido; el nuevo funciona.
    assert client.get("/api/auth/me", headers=Hv).status_code == 401
    Hn = {"Authorization": f"Bearer {r.json()['token']}"}
    assert client.get("/api/auth/me", headers=Hn).status_code == 200
    assert _login(client, "rot", "nuevaClave99").status_code == 200
    print("✓ Cambiar contraseña invalida los tokens anteriores")


def test_validate_requiere_key_y_rate_limit(client):
    T = _login(client, "admin", "admin123").json()["token"]
    H = {"Authorization": f"Bearer {T}"}
    r = client.post("/api/devices/register", headers=H, json={"name": "RL"}).json()
    dev, key = r["device_id"], r["api_key"]

    # 10 intentos con códigos inválidos desde la misma MAC → el 11º → 429.
    for i in range(10):
        rr = client.post(f"/api/devices/{dev}/codes/validate",
                         headers={"X-Api-Key": key}, json={"code": f"NOEXISTE{i}", "mac": "aa:bb:cc"})
        assert rr.status_code == 200 and rr.json()["valid"] is False
    rr = client.post(f"/api/devices/{dev}/codes/validate",
                     headers={"X-Api-Key": key}, json={"code": "NOEXISTE", "mac": "aa:bb:cc"})
    assert rr.status_code == 429
    # Otra MAC sigue pudiendo validar (límite por cliente, no por router).
    rr = client.post(f"/api/devices/{dev}/codes/validate",
                     headers={"X-Api-Key": key}, json={"code": "NOEXISTE", "mac": "dd:ee:ff"})
    assert rr.status_code == 200
    print("✓ /validate: fuerza bruta por MAC frenada a los 10 intentos/min")


def test_signup_rate_limit(client):
    # 10 signups/hora por IP; el 11º → 429.
    ok = 0
    for i in range(10):
        r = client.post("/api/signup", json={
            "company_name": f"Empresa {i}", "username": f"emp{i}", "password": "clave12345"})
        assert r.status_code == 200, r.text
        ok += 1
    r = client.post("/api/signup", json={
        "company_name": "Una más", "username": "emp-extra", "password": "clave12345"})
    assert r.status_code == 429
    print(f"✓ Signup público: {ok} cuentas/hora por IP, luego 429")
