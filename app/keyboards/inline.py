"""Inline keyboards for the bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Main menu inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Легковой", callback_data="light_vehicle"),
                InlineKeyboardButton(text="Грузовой", callback_data="cargo_vehicle")
            ],
            [
                InlineKeyboardButton(text="Акции", callback_data="promotions"),
            ]
        ]
    )


def get_license_options_light() -> InlineKeyboardMarkup:
    """License options inline keyboard for light vehicles."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Бесплатная оклейка", callback_data="wrap"),
                InlineKeyboardButton(text="Платная оклейка", callback_data="paid_wrap")
            ],
            [
                InlineKeyboardButton(text="Переклейка устаревшего бренда", callback_data="re_wrap")
            ],
            [
                InlineKeyboardButton(text="Назад", callback_data="back"),
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ]
    )


def get_no_license_options() -> InlineKeyboardMarkup:
    """No license options inline keyboard for light vehicles."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="4 000 руб. — Светоотражающие полосы + шашечный пояс", callback_data="reflective_strips")
            ],
            [
                InlineKeyboardButton(text="От 25 000 руб. — Полная оклейка по ГОСТ СПб", callback_data="full_wrap_gost")
            ],
            [
                InlineKeyboardButton(text="Назад", callback_data="back"),
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ]
    )


def get_yes_no_menu() -> InlineKeyboardMarkup:
    """Yes/No inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="yes"),
                InlineKeyboardButton(text="Нет", callback_data="no")
            ],
            [
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ]
    )


def get_license_yes_no_menu() -> InlineKeyboardMarkup:
    """Specialized yes/no keyboard for the license question."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="license_yes"),
                InlineKeyboardButton(text="Нет", callback_data="license_no")
            ],
            [
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ]
    )


def get_cancel_menu() -> InlineKeyboardMarkup:
    """Cancel inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ]
    )


def get_back_cancel_menu() -> InlineKeyboardMarkup:
    """Back/Cancel inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
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


def get_template_navigation(current_index: int, total_templates: int) -> InlineKeyboardMarkup:
    """Template navigation keyboard."""
    buttons = []
    
    # Navigation buttons
    nav_row = []
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"template_prev_{current_index}"))
    
    nav_row.append(InlineKeyboardButton(text=f"{current_index + 1}/{total_templates}", callback_data="template_current"))
    
    if current_index < total_templates - 1:
        nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"template_next_{current_index}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Action buttons
    action_row = [
        InlineKeyboardButton(text="Мой вариант", callback_data=f"template_select_{current_index}"),
        InlineKeyboardButton(text="Отмена", callback_data="cancel")
    ]
    buttons.append(action_row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
