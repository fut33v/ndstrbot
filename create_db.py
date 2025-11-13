#!/usr/bin/env python3
"""Database initialization script."""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.db import init_db
from infra.config import settings


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Initializing database with type: {settings.database_type}")
    logger.info(f"Database URL: {settings.database_url}")
    
    await init_db()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())