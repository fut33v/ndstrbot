"""Inline keyboards for the bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_license_options() -> InlineKeyboardMarkup:
    """License options inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Оклейка", callback_data="wrap"),
                InlineKeyboardButton(text="Переклейка", callback_data="re_wrap")
            ],
            [
                InlineKeyboardButton(text="Платная оклейка", callback_data="paid_wrap")
            ],
            [
                InlineKeyboardButton(text="Назад", callback_data="back"),
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ]
    )


def get_admin_request_actions(request_id: int) -> InlineKeyboardMarkup:
    """Admin actions for request."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Approve", callback_data=f"approve_{request_id}"),
                InlineKeyboardButton(text="Reject", callback_data=f"reject_{request_id}")
            ]
        ]
    )