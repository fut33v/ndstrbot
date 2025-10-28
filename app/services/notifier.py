"""Notification service."""

from typing import List
from aiogram import Bot

from infra.config import settings


async def notify_admins(bot: Bot, text: str, reply_markup=None):
    """
    Notify all admins.
    
    Args:
        bot: Telegram bot instance
        text: Notification text
        reply_markup: Optional reply markup
    """
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error notifying admin {admin_id}: {e}")


async def notify_user(bot: Bot, user_id: int, text: str):
    """
    Notify a specific user.
    
    Args:
        bot: Telegram bot instance
        user_id: User Telegram ID
        text: Notification text
    """
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except Exception as e:
        print(f"Error notifying user {user_id}: {e}")