"""Database initialization and session management."""

import logging
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from infra.config import settings
from domain.models import User, Request, File, Audit, Admin  # noqa: F401


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
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables initialized successfully")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    logger.debug("Creating async session")
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        logger.debug("Async session created successfully")
        yield session
        logger.debug("Async session yielded")
    logger.debug("Async session context closed")