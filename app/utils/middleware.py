"""Bot middleware."""

import logging
from typing import Any, Awaitable, Callable, Dict
from datetime import datetime
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db import get_session
from domain.models import User
from sqlmodel import select


logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """Middleware for user management."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process incoming events."""
        # Handle both Message and CallbackQuery events
        user_obj = None
        event_date = None
        if isinstance(event, Message):
            user_obj = event.from_user
            event_date = event.date
            logger.info("Starting UserMiddleware processing for message")
        elif isinstance(event, CallbackQuery):
            user_obj = event.from_user
            event_date = event.message.date if event.message else None
            logger.info("Starting UserMiddleware processing for callback query")
        
        if user_obj:
            try:
                # Create a new session for this request using context manager
                logger.debug("Creating database session")
                async with get_session() as session:
                    logger.debug("Database session created successfully")
                    data["session"] = session
                    
                    # Get or create user
                    tg_id = user_obj.id
                    logger.debug(f"Fetching user with tg_id: {tg_id}")
                    statement = select(User).where(User.tg_id == tg_id)
                    result = await session.execute(statement)
                    user = result.scalar_one_or_none()
                    
                    if not user:
                        logger.info(f"Creating new user with tg_id: {tg_id}")
                        user = User(
                            tg_id=tg_id,
                            username=user_obj.username,
                            first_name=user_obj.first_name,
                            last_name=user_obj.last_name
                        )
                        session.add(user)
                        await session.commit()
                        await session.refresh(user)
                        logger.debug(f"New user created with id: {user.id}")
                    else:
                        # Update last seen and explicitly load all attributes to avoid lazy loading issues
                        logger.debug(f"Updating last_seen for user id: {user.id}")
                        if event_date:
                            user.last_seen = event_date
                            await session.commit()
                        
                        # Explicitly refresh the user object to load all attributes
                        await session.refresh(user)
                    
                    data["user"] = user
                    
                    # Call handler and store the result
                    logger.debug("Calling handler")
                    result = await handler(event, data)
                    logger.debug("Handler completed successfully")
                    return result
            except Exception as e:
                logger.error(f"Error in UserMiddleware: {e}", exc_info=True)
                raise
        else:
            # For other types of events, just call the handler
            return await handler(event, data)