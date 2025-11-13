"""Start handler."""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards.inline import get_main_menu
from domain.models import User


logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, user: User):
    """Handle /start command."""
    logger.info(f"Start handler called for user {user.tg_id}")
    try:
        await message.answer(
            f"👋 Привет, {user.first_name}!\n"
            "🤖 Я бот для регистрации автомобилей в Яндекс GO.\n"
            "🛣 Выберите тип транспорта:",
            reply_markup=get_main_menu()
        )
        logger.debug("Start handler completed successfully")
    except Exception as e:
        logger.error(f"Error in start handler: {e}", exc_info=True)
        raise