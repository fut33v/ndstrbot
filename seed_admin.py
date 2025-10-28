#!/usr/bin/env python3
"""Script to seed admin users."""

import asyncio
import logging

from infra.db import init_db, get_session
from domain.models import User

async def main():
    """Seed admin users."""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    await init_db()
    
    # Add admin users
    # Note: This is just an example. In practice, you would add real admin users.
    async with get_session() as session:
        # Example admin user
        admin_user = User(
            tg_id=123456789,
            username="admin",
            first_name="Admin",
            last_name="User"
        )
        
        # Check if user already exists
        # TODO: Implement actual user checking
        
        session.add(admin_user)
        await session.commit()
        logging.info("Admin user seeded successfully!")

if __name__ == "__main__":
    asyncio.run(main())