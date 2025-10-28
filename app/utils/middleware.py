"""Bot middleware."""

import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
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
        if isinstance(event, Message):
            logger.info("Starting UserMiddleware processing for message")
            
            try:
                # Create a new session for this request using context manager
                logger.debug("Creating database session")
                async with get_session() as session:
                    logger.debug("Database session created successfully")
                    data["session"] = session
                    
                    # Get or create user
                    tg_id = event.from_user.id
                    logger.debug(f"Fetching user with tg_id: {tg_id}")
                    statement = select(User).where(User.tg_id == tg_id)
                    result = await session.execute(statement)
                    user = result.scalar_one_or_none()
                    
                    if not user:
                        logger.info(f"Creating new user with tg_id: {tg_id}")
                        user = User(
                            tg_id=tg_id,
                            username=event.from_user.username,
                            first_name=event.from_user.first_name,
                            last_name=event.from_user.last_name
                        )
                        session.add(user)
                        await session.commit()
                        await session.refresh(user)
                        logger.debug(f"New user created with id: {user.id}")
                    else:
                        # Update last seen
                        logger.debug(f"Updating last_seen for user id: {user.id}")
                        user.last_seen = event.date
                        await session.commit()
                    
                    data["user"] = user
                    
                    # Call handler and store the result
                    logger.debug("Calling handler")
                    result = await handler(event, data)
                    logger.debug("Handler completed successfully")
                    return result
            except Exception as e:
                logger.error(f"Error in UserMiddleware: {e}", exc_info=True)
                raise