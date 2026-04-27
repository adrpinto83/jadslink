from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from config import get_settings

settings = get_settings()

# Use NullPool for testing/development with SQLite compatibility
# In production, use AsyncQueuePool or external pooling (PgBouncer)
# For now, we use NullPool which is compatible with both sync and async
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
    connect_args={
        "timeout": 30,           # Connection timeout
        "server_settings": {
            "application_name": "jadslink_api",
            "jit": "off",
        }
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
