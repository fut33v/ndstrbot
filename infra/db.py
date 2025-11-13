"""Database initialization and session management."""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from infra.config import settings
from domain.models import User, Request, File, Audit, Admin, Template  # noqa: F401


logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True
)


async def init_db():
    """Initialize database tables."""
    logger.info("Initializing database tables")
    # For PostgreSQL, we need to use a sync engine for table creation
    # because async table creation in SQLAlchemy has some limitations
    if settings.database_type == "postgresql":
        from sqlalchemy import create_engine as create_sync_engine
        sync_engine = create_sync_engine(settings.database_url.replace("+asyncpg", ""))
        SQLModel.metadata.create_all(sync_engine)
        sync_engine.dispose()
    else:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables initialized successfully")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    logger.debug("Creating async session")
    async with AsyncSession(engine) as session:
        logger.debug("Async session created successfully")
        yield session
        logger.debug("Async session yielded")
    logger.debug("Async session context closed")