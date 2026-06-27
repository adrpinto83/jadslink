from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from config import get_settings

settings = get_settings()

# PostgreSQL async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Verify connection before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    connect_args={
        "timeout": 10,
    }
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
