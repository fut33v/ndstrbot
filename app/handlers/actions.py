"""Actions handlers."""

from aiogram import Router, F
from aiogram.types import Message

from app.keyboards.reply import get_main_menu

# Text constants
ACTIONS_TEXT = "🎉 Актуальные акции появятся здесь. Напишите оператору @username или оставьте заявку через раздел 'Легковой/Грузовой'."

router = Router()


@router.message(F.text == "Акции")
async def actions_handler(message: Message):
    """Handle actions button."""
    await message.answer(
        ACTIONS_TEXT,
        reply_markup=get_main_menu()
    )