"""Main bot module."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from infra.config import settings
from infra.logging import setup_logging
from app.utils.middleware import UserMiddleware
from app.handlers import start, light, cargo, actions, admin, common


async def main():
    """Main bot function."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting bot application")
    
    # Initialize bot variable
    bot = None
    
    try:
        # Create bot and dispatcher
        logger.debug("Creating bot instance")
        bot = Bot(token=settings.bot_token)
        logger.debug("Creating memory storage")
        storage = MemoryStorage()
        logger.debug("Creating dispatcher")
        dp = Dispatcher(storage=storage)
        
        # Register middleware
        logger.debug("Registering UserMiddleware")
        dp.message.middleware(UserMiddleware())
        
        # Register handlers
        logger.debug("Registering handlers")
        dp.include_router(start.router)
        dp.include_router(light.router)
        dp.include_router(cargo.router)
        dp.include_router(actions.router)
        dp.include_router(admin.router)
        dp.include_router(common.router)
        
        # Start polling
        logger.info("Starting bot polling...")
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Bot polling error: {e}", exc_info=True)
            raise
    except Exception as e:
        logger.error(f"Bot initialization error: {e}", exc_info=True)
        raise
    finally:
        if bot:
            logger.info("Closing bot session")
            await bot.session.close()
        logger.info("Bot application shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())