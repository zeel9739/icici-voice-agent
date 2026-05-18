from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

_settings = get_settings()

_is_sqlite = _settings.DATABASE_URL.startswith("sqlite")

_engine = create_async_engine(
    _settings.DATABASE_URL,
    echo=_settings.DEBUG,
    future=True,
    # SQLite needs NullPool (no concurrent connections); PostgreSQL uses a real pool
    **( {"poolclass": NullPool}
        if _is_sqlite else
        {"pool_size": 5, "max_overflow": 10, "pool_pre_ping": True}
    ),
)

_SessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a transactional session per request."""
    async with _SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all_tables() -> None:
    """Create all tables on startup (idempotent)."""
    from app.db.base import Base
    import app.models  # noqa: F401 — ensures models are registered with Base

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
