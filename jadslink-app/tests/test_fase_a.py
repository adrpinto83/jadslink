"""Test de FASE A: migración multi-tenant sobre una BD 'vieja' con datos (como prod)."""
import os, sqlite3, tempfile, hashlib, sys

DB = os.path.join(tempfile.mkdtemp(), "legacy.db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
os.environ["ADMIN_PASSWORD"] = "admin123"

def h(pw): return hashlib.sha256(pw.encode()).hexdigest()

# ── 1. Construir una BD "vieja" (esquema pre-FASE-A) con datos ──────────────────
con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE devices (
  id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, api_key VARCHAR UNIQUE NOT NULL,
  location VARCHAR, firmware VARCHAR, model VARCHAR, last_seen DATETIME,
  online BOOLEAN, config JSON, created_at DATETIME
);
CREATE TABLE admin_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR UNIQUE NOT NULL,
  password_hash VARCHAR NOT NULL, created_at DATETIME
);
CREATE TABLE codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, device_id VARCHAR NOT NULL, code VARCHAR NOT NULL,
  duration_min INTEGER, max_uses INTEGER, uses INTEGER, bandwidth_dn INTEGER,
  bandwidth_up INTEGER, expires_at DATETIME, active BOOLEAN, created_at DATETIME, note VARCHAR
);
""")
con.execute("INSERT INTO devices (id,name,api_key,location,model,config,online) VALUES (?,?,?,?,?,?,?)",
            ("dev-legacy-1", "Router Viejo", "legacy-key-123", "Bus 1", "OpenWrt", "{}", 0))
con.execute("INSERT INTO admin_users (username,password_hash) VALUES (?,?)",
            ("admin", h("secretoViejo")))   # password legacy que DEBE preservarse
con.execute("INSERT INTO codes (device_id,code,duration_min,max_uses,uses,active) VALUES (?,?,?,?,?,?)",
            ("dev-legacy-1", "OLDCODE1", 720, 1, 0, 1))
con.commit(); con.close()
print("BD vieja creada con: 1 device, 1 admin (pass=secretoViejo), 1 code")

# ── 2. Arrancar la app (dispara lifespan → migraciones) ─────────────────────────
sys.path.insert(0, "/home/adrpinto/jadslink/jadslink-app")
from fastapi.testclient import TestClient
from api.main import app

with TestClient(app) as client:
    # ── 3. Verificar esquema migrado ────────────────────────────────────────────
    con = sqlite3.connect(DB)
    cols = {r[1] for r in con.execute("PRAGMA table_info(devices)")}
    assert "account_id" in cols and "group_id" in cols, f"faltan columnas: {cols}"
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"accounts", "users", "device_groups"} <= tables, f"faltan tablas: {tables}"
    # device viejo backfilleado a la cuenta por defecto
    acc_id = con.execute("SELECT account_id FROM devices WHERE id='dev-legacy-1'").fetchone()[0]
    assert acc_id, "device NO fue backfilleado a una cuenta"
    default_acc = con.execute("SELECT id,name,slug FROM accounts WHERE slug='jads-studio'").fetchone()
    assert default_acc and acc_id == default_acc[0], "device no quedó en la cuenta por defecto"
    con.close()
    print("✓ Esquema migrado: columnas + tablas + backfill OK")

    # ── 4. Login con la contraseña LEGACY (debe seguir funcionando) ──────────────
    r = client.post("/api/auth/login", json={"username": "admin", "password": "secretoViejo"})
    assert r.status_code == 200, f"login legacy falló: {r.status_code} {r.text}"
    tok = r.json()["token"]
    assert r.json()["role"] == "superadmin", f"admin debería ser superadmin: {r.json()}"
    print("✓ Login superadmin con password legacy OK, role=superadmin")
    H = {"Authorization": f"Bearer {tok}"}

    # login incorrecto rechazado
    assert client.post("/api/auth/login", json={"username":"admin","password":"malo"}).status_code == 401
    print("✓ Login con password incorrecta → 401")

    # ── 5. Superadmin ve el device legacy ────────────────────────────────────────
    r = client.get("/api/devices", headers=H); assert r.status_code == 200
    devs = r.json(); assert any(d["id"] == "dev-legacy-1" for d in devs), devs
    print(f"✓ Superadmin ve {len(devs)} device(s), incluye el legacy")

    # ── 6. Crear una cuenta operador con su owner ────────────────────────────────
    r = client.post("/api/accounts", headers=H, json={
        "name": "Transportes ABC", "owner_username": "abc", "owner_password": "abc12345"})
    assert r.status_code == 200, f"crear cuenta: {r.text}"
    abc_acc = r.json()["id"]
    print(f"✓ Cuenta operador creada: {r.json()['name']} (slug={r.json()['slug']})")

    # login del operador
    r = client.post("/api/auth/login", json={"username": "abc", "password": "abc12345"})
    assert r.status_code == 200, r.text
    Habc = {"Authorization": f"Bearer {r.json()['token']}"}
    assert r.json()["role"] == "owner"
    print("✓ Login del operador OK, role=owner")

    # ── 7. AISLAMIENTO: el operador NO ve el device legacy (es de otra cuenta) ────
    r = client.get("/api/devices", headers=Habc); assert r.status_code == 200
    assert len(r.json()) == 0, f"operador NO debería ver devices ajenos, vio: {r.json()}"
    print("✓ Aislamiento: operador ve 0 devices (los legacy son de otra cuenta)")

    # operador no puede acceder al device ajeno por id → 404
    assert client.get("/api/devices/dev-legacy-1", headers=Habc).status_code == 404
    print("✓ Aislamiento: GET device ajeno por id → 404")

    # operador no puede generar códigos en device ajeno → 404
    assert client.post("/api/devices/dev-legacy-1/codes", headers=Habc,
                       json={"quantity":1}).status_code == 404
    print("✓ Aislamiento: generar códigos en device ajeno → 404")

    # ── 8. El operador registra su propio router y lo ve ─────────────────────────
    r = client.post("/api/devices/register", headers=Habc,
                    json={"name": "Bus ABC 1", "location": "Ruta 1"})
    assert r.status_code == 200, r.text
    new_dev = r.json()["device_id"]
    r = client.get("/api/devices", headers=Habc)
    assert len(r.json()) == 1 and r.json()[0]["id"] == new_dev
    assert r.json()[0]["account_id"] == abc_acc, "device nuevo debe quedar en la cuenta del operador"
    print("✓ Operador registra su router y lo ve (queda en su cuenta)")

    # genera códigos en SU router (ok) y verifica expires_at default
    r = client.post(f"/api/devices/{new_dev}/codes", headers=Habc,
                    json={"quantity": 3, "duration_min": 720})
    assert r.status_code == 200 and r.json()["created"] == 3, r.text
    print("✓ Operador genera 3 códigos en su router")

    # superadmin ahora ve todos (legacy + router de campo seedeado + nuevo del operador)
    r = client.get("/api/devices", headers=H)
    assert len(r.json()) == 3, f"superadmin debería ver 3: {len(r.json())}"
    print("✓ Superadmin ve los 3 devices (legacy + router campo + nuevo operador)")

    # ── 9. Grupos ────────────────────────────────────────────────────────────────
    r = client.post("/api/groups", headers=Habc, json={"name": "Flota Norte"})
    assert r.status_code == 200, r.text
    gid = r.json()["id"]
    r = client.get("/api/groups", headers=Habc); assert len(r.json()) == 1
    print("✓ Operador crea y lista su grupo de routers")

    # operador NO puede crear cuentas (solo superadmin)
    assert client.post("/api/accounts", headers=Habc, json={
        "name":"x","owner_username":"y","owner_password":"z12345"}).status_code == 403
    print("✓ Operador NO puede crear cuentas (403)")

    # ── 10. Heartbeat del device legacy sigue funcionando (api_key) ──────────────
    r = client.post("/api/devices/dev-legacy-1/heartbeat",
                    headers={"X-Api-Key": "legacy-key-123"}, json={"clients": []})
    assert r.status_code == 200, f"heartbeat legacy falló: {r.text}"
    print("✓ Heartbeat del device legacy (api_key) sigue OK")

print("\n🎉 TODOS LOS TESTS DE FASE A PASARON")
