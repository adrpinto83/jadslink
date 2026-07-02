from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Directorio de datos persistentes (BD SQLite, comprobantes, secretos generados).
# En producción conviene apuntarlo FUERA del árbol de deploy para sobrevivir redeploys.
DATA_DIR = os.path.abspath(os.getenv(
    "DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data")
))
os.makedirs(DATA_DIR, exist_ok=True)

_default_db = os.path.join(DATA_DIR, "hotspot.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_default_db}")


def _make_engine(url: str):
    is_sqlite = url.startswith("sqlite")
    kwargs = {"connect_args": {"check_same_thread": False}} if is_sqlite else {"pool_pre_ping": True}
    eng = create_engine(url, **kwargs)
    if is_sqlite:
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_connection, _):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")
            dbapi_connection.execute("PRAGMA journal_mode=WAL")
    return eng


engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def configure(url: str):
    """Reapunta el engine a otra BD (usado por los tests). Muta SessionLocal
    en el sitio para que las referencias ya importadas sigan siendo válidas."""
    global engine, DATABASE_URL
    if engine is not None:
        engine.dispose()
    DATABASE_URL = url
    engine = _make_engine(url)
    SessionLocal.configure(bind=engine)
    return engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
