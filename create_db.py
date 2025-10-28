#!/usr/bin/env python3
"""Database initialization script."""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.db import init_db

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())