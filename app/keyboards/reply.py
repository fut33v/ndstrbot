"""Reply keyboards for the bot."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Легковой"),
                KeyboardButton(text="Грузовой")
            ],
            [
                KeyboardButton(text="Акции"),
            ]
        ],
        resize_keyboard=True
    )


def get_yes_no_menu() -> ReplyKeyboardMarkup:
    """Yes/No keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Да"),
                KeyboardButton(text="Нет")
            ],
            [
                KeyboardButton(text="Отмена")
            ]
        ],
        resize_keyboard=True
    )


def get_cancel_menu() -> ReplyKeyboardMarkup:
    """Cancel keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Отмена")
            ]
        ],
        resize_keyboard=True
    )


def get_back_cancel_menu() -> ReplyKeyboardMarkup:
    """Back/Cancel keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Назад"),
                KeyboardButton(text="Отмена")
            ]
        ],
        resize_keyboard=True
    )