from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from config import get_settings

settings = get_settings()

# Configurar connect_args según el tipo de base de datos
connect_args = {}
if "postgresql" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL:
    # PostgreSQL con asyncpg no necesita charset
    connect_args = {}
else:
    # MySQL con aiomysql
    connect_args = {
        "charset": "utf8mb4",
        "autocommit": True,
    }

# Use QueuePool for connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Verify connection before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    connect_args=connect_args
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
