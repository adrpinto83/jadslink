"""Test de FASE C: pagos con comprobante, aprobación que extiende el ciclo, y vencimientos."""
from datetime import datetime, timedelta


def test_fase_c(client):
    from api.database import SessionLocal
    from api.models import Account
    from api import billing

    T = client.post("/api/auth/login", json={"username":"admin","password":"admin123"}).json()["token"]
    H = {"Authorization": f"Bearer {T}"}

    # ── 1. Crear cuenta Pro (ciclo de cortesía de 30 días) ───────────────────────
    acc_id = client.post("/api/accounts", headers=H, json={
        "name":"Playa Pro","plan":"pro","contact_phone":"+58412...",
        "owner_username":"pp","owner_password":"pp123456"}).json()["id"]
    Ho = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username':'pp','password':'pp123456'}).json()['token']}"}

    me = client.get("/api/auth/me", headers=Ho).json()
    bi = me["account"]["billing"]
    assert bi["billing_cycle_end"] and 28 <= bi["days_left"] <= 30 and not bi["expired"], bi
    print(f"✓ Cuenta Pro creada con ciclo inicial ({bi['days_left']} días restantes)")

    # ── 2. Reportar pago con comprobante (multipart) ─────────────────────────────
    proof = ("comprobante.png", b"\x89PNG\r\n\x1a\n fake image bytes", "image/png")
    r = client.post(f"/api/accounts/{acc_id}/payments", headers=Ho,
                    data={"amount_usd":"29","method":"pago_movil","reference":"REF12345","note":"Enero"},
                    files={"proof": proof})
    assert r.status_code==200, r.text
    pay_id = r.json()["id"]
    assert r.json()["status"]=="pending" and r.json()["has_proof"] is True
    print("✓ Operador reporta pago con comprobante (pending)")

    # método inválido rechazado
    assert client.post(f"/api/accounts/{acc_id}/payments", headers=Ho,
                      data={"amount_usd":"29","method":"bitcoin"}).status_code==400
    print("✓ Método de pago inválido → 400")

    # ── 3. El superadmin ve la cola de pendientes ────────────────────────────────
    pend = client.get("/api/payments?status=pending", headers=H).json()
    assert any(p["id"]==pay_id and p["account_name"]=="Playa Pro" for p in pend), pend
    print(f"✓ Superadmin ve {len(pend)} pago(s) pendiente(s) con nombre de cuenta")

    # comprobante accesible por superadmin
    assert client.get(f"/api/payments/{pay_id}/proof", headers=H).status_code==200
    print("✓ Superadmin puede ver el comprobante")

    # ── 4. Aprobar → extiende el ciclo ~30 días y deja la cuenta activa ──────────
    before = client.get("/api/auth/me", headers=Ho).json()["account"]["billing"]["days_left"]
    r = client.post(f"/api/payments/{pay_id}/approve", headers=H)
    assert r.status_code==200 and r.json()["account_status"]=="active", r.text
    after = client.get("/api/auth/me", headers=Ho).json()["account"]["billing"]["days_left"]
    assert after > before, f"el ciclo debía extenderse: {before} -> {after}"
    print(f"✓ Aprobado: ciclo extendido ({before} → {after} días)")

    # aprobar de nuevo el mismo pago → 400
    assert client.post(f"/api/payments/{pay_id}/approve", headers=H).status_code==400
    print("✓ Re-aprobar el mismo pago → 400")

    # ── 5. Un operador NO puede aprobar pagos ni ver la cola global ──────────────
    assert client.get("/api/payments", headers=Ho).status_code==403
    assert client.post(f"/api/payments/{pay_id}/approve", headers=Ho).status_code==403
    print("✓ Operador no accede a la cola ni aprueba (403)")

    # aislamiento: otro operador no ve/paga esta cuenta
    client.post("/api/accounts", headers=H, json={
        "name":"Otro","plan":"starter","owner_username":"ot","owner_password":"ot123456"})
    Hot = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username':'ot','password':'ot123456'}).json()['token']}"}
    assert client.get(f"/api/accounts/{acc_id}/payments", headers=Hot).status_code==404
    print("✓ Aislamiento: operador ajeno no ve pagos de otra cuenta (404)")

    # ── 6. Rechazo de pago ────────────────────────────────────────────────────────
    p2 = client.post(f"/api/accounts/{acc_id}/payments", headers=Ho,
                     data={"amount_usd":"5","method":"zelle","reference":"X"}).json()["id"]
    assert client.post(f"/api/payments/{p2}/reject", headers=H, json={"note":"monto insuficiente"}).status_code==200
    hist = client.get(f"/api/accounts/{acc_id}/payments", headers=Ho).json()
    rej = next(p for p in hist if p["id"]==p2)
    assert rej["status"]=="rejected" and rej["review_note"]=="monto insuficiente"
    print("✓ Rechazo de pago con nota registrado")

    # ── 7. Vencimiento automático (run_billing_cycle) ────────────────────────────
    db = SessionLocal()
    a = db.query(Account).filter(Account.id==acc_id).first()
    # forzar vencimiento dentro de la gracia → past_due
    a.billing_cycle_end = datetime.utcnow() - timedelta(days=2); db.commit()
    billing.run_billing_cycle(db); db.refresh(a)
    assert a.status=="past_due", f"esperaba past_due, got {a.status}"
    print("✓ Vencida dentro de gracia → past_due")

    # pasada la gracia → suspended
    a.billing_cycle_end = datetime.utcnow() - timedelta(days=billing.GRACE_DAYS+1); db.commit()
    billing.run_billing_cycle(db); db.refresh(a)
    assert a.status=="suspended", f"esperaba suspended, got {a.status}"
    print("✓ Pasada la gracia → suspended")

    # cuenta con billing_cycle_end=NULL (JADS Studio) nunca se toca
    jads = db.query(Account).filter(Account.slug=="jads-studio").first()
    assert jads.billing_cycle_end is None and jads.status=="active"
    billing.run_billing_cycle(db); db.refresh(jads)
    assert jads.status=="active", "JADS Studio (sin vencimiento) no debe suspenderse"
    print("✓ Cuenta sin vencimiento (JADS Studio) nunca se suspende")
    db.close()

    # ── 8. Suspendida por impago bloquea generar códigos (integración FASE B) ────
    dev = client.post("/api/devices/register", headers=H, json={"name":"D","account_id":acc_id}).json()["device_id"]
    assert client.post(f"/api/devices/{dev}/codes", headers=Ho, json={"quantity":1}).status_code==403
    print("✓ Cuenta suspendida por impago → no genera códigos (403)")

    print("\n🎉 TODOS LOS TESTS DE FASE C PASARON")
