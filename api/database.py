from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=QueuePool,
    pool_size=20,           # Conexiones mantenidas en el pool
    max_overflow=10,        # Conexiones adicionales cuando pool está lleno
    pool_timeout=30,        # Tiempo de espera para obtener conexión (segundos)
    pool_recycle=3600,      # Reciclar conexiones cada hora (evita idle timeout)
    pool_pre_ping=True,     # Verificar conexión antes de usarla
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency for FastAPI endpoints to get database session"""
    async with async_session_maker() as session:
        yield session
