from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Runtime engine — connects as the least-privilege sajilo_app role so that
# Postgres Row-Level Security policies are actually enforced for every
# request. Migrations connect separately as the admin/table-owner role
# (settings.DATABASE_URL) — see alembic/env.py. Never merge these two.
engine = create_async_engine(
    settings.APP_DATABASE_URL,
    pool_size=5,
    max_overflow=5,       # 10 max, comfortably under Postgres max_connections=20
    pool_recycle=1800,
    pool_pre_ping=True,   # local round trip, cheap insurance
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session