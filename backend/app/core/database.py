from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def init_database_schema(target_engine=None) -> None:
    import logging
    from sqlalchemy import text

    logger = logging.getLogger(__name__)
    eng = target_engine or engine
    from app import models as _app_models  # noqa: F401
    from app.agents import models as _agent_models  # noqa: F401

    async with eng.begin() as conn:
        for ext in ("vector", "pgcrypto"):
            try:
                await conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext}"))
            except Exception as ext_err:
                logger.warning(f"Could not enable extension {ext}: {ext_err}")

        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as schema_err:
            logger.warning(f"Full create_all failed ({schema_err}), creating tables individually...")
            for table in Base.metadata.sorted_tables:
                try:
                    await conn.run_sync(table.create, checkfirst=True)
                except Exception as tbl_err:
                    logger.warning(f"Failed to create table {table.name}: {tbl_err}")
