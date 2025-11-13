"""Actions handlers."""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.keyboards.inline import get_main_menu

# Text constants
ACTIONS_TEXT = "🎉 Актуальные акции появятся здесь. Напишите оператору @username или оставьте заявку через раздел 'Легковой/Грузовой'."

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "promotions")
async def actions_handler(callback: CallbackQuery):
    """Handle actions button."""
    logger.info(f"Actions handler called with callback data: '{callback.data}'")
    if callback.message:
        try:
            await callback.message.edit_text(
                ACTIONS_TEXT,
                reply_markup=get_main_menu()
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback.answer("Ошибка при обработке запроса")
            return
    await callback.answer()