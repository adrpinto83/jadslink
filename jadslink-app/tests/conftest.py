"""Fixtures compartidas: cada test corre contra una BD SQLite nueva y aislada.

El engine de la app es global, así que `fresh_db` lo reapunta con
`database.configure()` antes de levantar el TestClient (cuyo `with` dispara el
lifespan: create_all + migraciones + seeds).
"""
import os, sys, json, tempfile

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)

# Config de test ANTES de importar la app.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="jadslink-test-data-")
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["JWT_SECRET"] = "test-secret-not-for-prod"
os.environ["PUBLIC_URL"] = "https://link.jadsstudio.com"
os.environ["SEED_DEVICES_JSON"] = json.dumps([{
    "id": "test-field-router",
    "name": "Router Campo (seed test)",
    "api_key": "test-field-router-key",
    "location": "Test",
    "model": "OpenWrt",
}])

import pytest


@pytest.fixture()
def fresh_db(tmp_path):
    """Reapunta el engine global a una BD nueva y limpia los rate limits."""
    from api import database, ratelimit
    db_file = tmp_path / "test.db"
    database.configure(f"sqlite:///{db_file}")
    ratelimit.reset()
    return str(db_file)


@pytest.fixture()
def client(fresh_db):
    """TestClient con lifespan (migraciones + seeds) sobre la BD fresca."""
    from fastapi.testclient import TestClient
    from api.main import app
    with TestClient(app) as c:
        yield c
