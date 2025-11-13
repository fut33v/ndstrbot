"""Light vehicle handlers."""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlmodel import select

from app.states.light import LightVehicleStates
from app.keyboards.inline import (
    get_main_menu,
    get_yes_no_menu,
    get_license_options_light,
    get_template_navigation,
    get_cancel_menu,
    get_no_license_options,
    get_license_yes_no_menu,
)
from app.services.validators import validate_year
from domain.models import Request, Template
from infra.config import settings

# Text constants
BRAND_Q = "Есть ли сейчас у вас бренд?"
SEND4_AUTO = "Отправьте 4 фото автомобиля: спереди, сзади, слева и справа."
YEAR_Q = "Укажите год выпуска вашего авто (1980–{current_year})."
LICENSE_Q = "Есть ли лицензия?"
OPTIONS_TEXT = "Варианты: оклейка, переклейка и платной оклейки."
LICENSE_WRAP = "Оклейка для получения лицензии."
NO_LICENSE_OPTIONS_TEXT = "Выберите вариант оклейки:"
REFLECTIVE_STRIPS = "4 000 руб. — Светоотражающие полосы + шашечный пояс"
FULL_WRAP_GOST = "От 25 000 руб. — Полная оклейка для получения лицензии по ГОСТ СПб"
RE_WRAP_MESSAGE = "Вы выбрали переклейку устаревшего бренда. Сейчас живая очередь, как только подойдет ваша очередь, мы вам напишем и пригласим на мойку 🧽"
THANKS = "Спасибо! Мы свяжемся с вами и пригласим на ближайшую дату."
INVALID_PHOTO = "Пожалуйста, пришлите фото (JPEG/PNG)."
CANCELLED = "Заявка отменена. Чтобы начать заново — /start."
BACK_TEXT = "Шаг назад. Продолжим."

logger = logging.getLogger(__name__)

router = Router()


LICENSE_OPTION_LABELS = {
    "wrap": "Бесплатная оклейка",
    "paid_wrap": "Платная оклейка",
}

NO_LICENSE_OPTION_LABELS = {
    "reflective_strips": REFLECTIVE_STRIPS,
    "full_wrap_gost": FULL_WRAP_GOST,
}


async def _show_license_options(state: FSMContext, send_message):
    """Persist license flag and prompt available wrap options."""
    await state.update_data(has_license=True)
    await state.set_state(LightVehicleStates.choosing_license_option)
    if send_message:
        await send_message(
            OPTIONS_TEXT,
            reply_markup=get_license_options_light()
        )


async def _prompt_no_license_options(state: FSMContext, send_message):
    """Ask user to choose a wrap flow when no license is available."""
    await state.update_data(has_license=False)
    await state.set_state(LightVehicleStates.choosing_no_license_option)
    if send_message:
        await send_message(
            f"{LICENSE_WRAP}\n\n{NO_LICENSE_OPTIONS_TEXT}",
            reply_markup=get_no_license_options()
        )


async def _create_request_record(
    state: FSMContext,
    session,
    user,
    *,
    has_license: bool,
    auto_submit: bool = False,
    **extra_fields,
) -> Request:
    """Persist a light-vehicle request and cache its id in state."""
    data = await state.get_data()
    request = Request(
        user_id=user.id,
        category="легковой",
        has_brand=data.get("has_brand"),
        year=data.get("year"),
        has_license=has_license,
        **extra_fields,
    )
    if auto_submit:
        request.status = "submitted"
        request.submitted_at = datetime.utcnow()
    session.add(request)
    await session.commit()
    await session.refresh(request)
    await state.update_data(request_id=request.id)
    return request


async def _finalize_request_without_photos(state: FSMContext, notify_func, request: Request):
    """Send final confirmation and reset state for no-brand flows."""
    if notify_func:
        await notify_func(
            THANKS + f"\n\nВаша заявка: #REQ-{request.id}"
        )
    await state.clear()


@router.callback_query(F.data == "light_vehicle")
async def start_light_vehicle_callback(callback: CallbackQuery, state: FSMContext, session, user):
    """Start light vehicle registration process via callback."""
    logger.info(f"Light vehicle callback handler called with data: '{callback.data}'")
    await state.set_state(LightVehicleStates.choosing_brand)
    if callback.message:
        try:
            await callback.message.edit_text(
                BRAND_Q,
                reply_markup=get_yes_no_menu()
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            # If we can't edit, send a new message
            await callback.message.answer(
                BRAND_Q,
                reply_markup=get_yes_no_menu()
            )
    await callback.answer()


@router.message(F.text == "Легковой")
async def start_light_vehicle(message: Message, state: FSMContext):
    """Start light vehicle registration process."""
    logger.info(f"Light vehicle handler called with text: '{message.text}'")
    await state.set_state(LightVehicleStates.choosing_brand)
    await message.answer(
        BRAND_Q,
        reply_markup=get_yes_no_menu()
    )


@router.callback_query(F.data == "yes")
async def brand_yes_callback(callback: CallbackQuery, state: FSMContext, session, user):
    """Handle 'Yes' to brand question via callback."""
    logger.info("Brand yes callback handler called")
    # Save user choice
    await state.update_data(has_brand=True)
    
    # Create request
    request = Request(
        user_id=user.id,
        category="легковой",
        has_brand=True
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    
    # Save request ID in state
    await state.update_data(request_id=request.id)
    
    # Move to photo sending state
    await state.set_state(LightVehicleStates.sending_photos)
    if callback.message:
        try:
            await callback.message.edit_text(
                SEND4_AUTO,
                reply_markup=get_cancel_menu()
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            # If we can't edit, send a new message
            await callback.message.answer(
                SEND4_AUTO,
                reply_markup=get_cancel_menu()
            )
    await callback.answer()


@router.callback_query(F.data == "no")
async def brand_no_callback(callback: CallbackQuery, state: FSMContext):
    """Handle 'No' to brand question via callback."""
    logger.info("Brand no callback handler called")
    await state.update_data(has_brand=False)
    await state.set_state(LightVehicleStates.entering_year)
    if callback.message:
        try:
            await callback.message.edit_text(
                YEAR_Q.format(current_year=2025),  # TODO: Use actual current year
                reply_markup=get_cancel_menu()
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            # If we can't edit, send a new message
            await callback.message.answer(
                YEAR_Q.format(current_year=2025),  # TODO: Use actual current year
                reply_markup=get_cancel_menu()
            )
    await callback.answer()


@router.message(LightVehicleStates.entering_year)
async def enter_year(message: Message, state: FSMContext):
    """Handle year input."""
    logger.info("Enter year handler called")
    if message.text is None:
        await message.answer("Пожалуйста, введите корректный год (1980-2025)")
        return
    is_valid, year = validate_year(message.text)
    
    if not is_valid:
        await message.answer("Пожалуйста, введите корректный год (1980-2025)")
        return
    
    await state.update_data(year=year)
    await state.set_state(LightVehicleStates.choosing_license)
    await message.answer(
        LICENSE_Q,
        reply_markup=get_license_yes_no_menu()
    )


@router.message(LightVehicleStates.choosing_license, F.text == "Да")
async def license_yes(message: Message, state: FSMContext):
    """Handle 'Yes' to license question."""
    logger.info("License yes handler called")
    await _show_license_options(state, message.answer)


@router.message(LightVehicleStates.choosing_license, F.text == "Нет")
async def license_no(message: Message, state: FSMContext):
    """Handle 'No' to license question."""
    logger.info("License no handler called")
    await _prompt_no_license_options(state, message.answer)


@router.callback_query(StateFilter(LightVehicleStates.choosing_license), F.data == "license_yes")
async def license_yes_callback(callback: CallbackQuery, state: FSMContext):
    """Handle inline 'Yes' selection for license question."""
    logger.info("License yes callback handler called")
    if callback.message:
        await _show_license_options(state, callback.message.edit_text)
    await callback.answer()


@router.callback_query(StateFilter(LightVehicleStates.choosing_license), F.data == "license_no")
async def license_no_callback(callback: CallbackQuery, state: FSMContext):
    """Handle inline 'No' selection for license question."""
    logger.info("License no callback handler called")
    if callback.message:
        await _prompt_no_license_options(state, callback.message.edit_text)
    await callback.answer()


@router.callback_query(
    StateFilter(LightVehicleStates.choosing_license_option),
    F.data.in_({"wrap", "paid_wrap"})
)
async def other_license_options_selected(callback: CallbackQuery, state: FSMContext, session, user):
    """Handle other license option selections."""
    logger.info(f"License option selected: {callback.data}")
    option_code = callback.data or ""
    option_text = LICENSE_OPTION_LABELS.get(option_code, option_code)
    await state.update_data(license_option=option_code)
    request = await _create_request_record(
        state,
        session,
        user,
        has_license=True,
        auto_submit=True
    )
    
    try:
        if callback.message:
            try:
                await callback.message.edit_text(f"Выбрано: {option_text}")
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                # If we can't edit, send a new message
                await callback.message.answer("Выбрано: " + (callback.data or ""))
        await _finalize_request_without_photos(
            state,
            callback.message.answer if callback.message else None,
            request
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await callback.answer("Ошибка при обработке запроса")
        return
    await callback.answer()


@router.callback_query(
    StateFilter(LightVehicleStates.choosing_no_license_option),
    F.data.in_({"reflective_strips", "full_wrap_gost"})
)
async def no_license_option_selected(callback: CallbackQuery, state: FSMContext, session, user):
    """Handle wrap choices for drivers who don't yet have a license."""
    logger.info(f"No-license option selected: {callback.data}")
    option_code = callback.data or ""
    option_text = NO_LICENSE_OPTION_LABELS.get(option_code, option_code)
    await state.update_data(no_license_option=option_code)
    request = await _create_request_record(
        state,
        session,
        user,
        has_license=False,
        auto_submit=True
    )
    try:
        if callback.message:
            try:
                await callback.message.edit_text(f"Выбрано: {option_text}\n\n{LICENSE_WRAP}")
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                await callback.message.answer(f"Выбрано: {option_text}\n\n{LICENSE_WRAP}")
        await _finalize_request_without_photos(
            state,
            callback.message.answer if callback.message else None,
            request
        )
    except Exception as e:
        logger.error(f"Error processing no-license option: {e}")
        await callback.answer("Ошибка при обработке запроса")
        return
    await callback.answer()


@router.callback_query(F.data == "re_wrap")
async def re_wrap_selected(callback: CallbackQuery, state: FSMContext, session, user, bot):
    """Handle re-wrap option selection - show template selection."""
    logger.info("Re-wrap option selected")
    
    # Get all templates from database that have valid file_ids
    statement = select(Template)
    result = await session.execute(statement)
    all_templates = result.scalars().all()
    
    # Filter templates to only include those with valid file_ids or valid image paths
    templates = [t for t in all_templates if t.file_id or (t.path and t.path.lower().endswith(('.png', '.jpg', '.jpeg')))]
    
    if not templates:
        # No templates available, fallback to regular flow
        try:
            if callback.message:
                await callback.message.answer("❌ Нет доступных шаблонов. Продолжаем обычный процесс.")
            request = await _create_request_record(
                state,
                session,
                user,
                has_license=True,
                auto_submit=True
            )
            if callback.message:
                await callback.message.answer("✅ Выбрано: re_wrap (без шаблонов)")
            await _finalize_request_without_photos(
                state,
                callback.message.answer if callback.message else None,
                request
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback.answer("Ошибка при обработке запроса")
            return
        await callback.answer()
        return
    
    # Show first template with navigation
    template = templates[0]
    
    # Save templates and current index in state
    await state.update_data(
        templates=[t.id for t in templates],
        current_template_index=0
    )
    
    # Send template image
    try:
        # Check if template has a Telegram file_id or a local path
        if template.file_id:
            # Use Telegram file ID
            photo = template.file_id
        else:
            # Use local file path - extract filename from path
            filename = template.path.split('/')[-1]
            # Use the web app base URL from settings
            photo = f"{settings.web_app_base_url}/uploads/{filename}"
        
        if callback.message:
            sent_message = await callback.message.answer_photo(
                photo=photo,
                caption=f"Шаблон {template.name}\n\n{template.description or ''}",
                reply_markup=get_template_navigation(0, len(templates))
            )
            # Store message ID for later updates
            await state.update_data(template_message_id=sent_message.message_id)
    except Exception as e:
        logger.error(f"Error sending template: {e}")
        await callback.answer("Ошибка при отправке шаблона")
        return
    
    await callback.answer()


@router.callback_query(F.data.startswith("template_prev_"))
async def template_prev(callback: CallbackQuery, state: FSMContext, session, user, bot):
    """Handle template previous navigation."""
    logger.info(f"Template previous: {callback.data}")
    
    # Get current state data
    data = await state.get_data()
    templates = data.get("templates", [])
    current_index = data.get("current_template_index", 0)
    
    if not templates:
        await callback.answer("Нет шаблонов для навигации")
        return
    
    # Move to previous template
    new_index = max(0, current_index - 1)
    if new_index == current_index:
        await callback.answer()
        return
    
    # Get template
    statement = select(Template).where(Template.id == templates[new_index])
    result = await session.execute(statement)
    template = result.scalar_one_or_none()
    
    if not template:
        await callback.answer("Шаблон не найден")
        return
    
    # Update state
    await state.update_data(current_template_index=new_index)
    
    # Update message with new template
    try:
        # Check if template has a Telegram file_id or a local path
        if template.file_id:
            # Use Telegram file ID
            photo = template.file_id
        else:
            # Use local file path - extract filename from path
            filename = template.path.split('/')[-1]
            # Use the web app base URL from settings
            photo = f"{settings.web_app_base_url}/uploads/{filename}"
        
        if callback.message:
            # Delete the previous message and send a new one with the updated template
            try:
                await callback.message.delete()
            except Exception as e:
                logger.warning(f"Could not delete template message: {e}")
            
            # Send new template message
            sent_message = await callback.message.answer_photo(
                photo=photo,
                caption=f"Шаблон {template.name}\n\n{template.description or ''}",
                reply_markup=get_template_navigation(new_index, len(templates))
            )
            # Update message ID in state
            await state.update_data(template_message_id=sent_message.message_id)
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        await callback.answer("Ошибка при обновлении шаблона")
        return
    
    await callback.answer()


@router.callback_query(F.data.startswith("template_next_"))
async def template_next(callback: CallbackQuery, state: FSMContext, session, user, bot):
    """Handle template next navigation."""
    logger.info(f"Template next: {callback.data}")
    
    # Get current state data
    data = await state.get_data()
    templates = data.get("templates", [])
    current_index = data.get("current_template_index", 0)
    
    if not templates:
        await callback.answer("Нет шаблонов для навигации")
        return
    
    # Move to next template
    new_index = min(len(templates) - 1, current_index + 1)
    if new_index == current_index:
        await callback.answer()
        return
    
    # Get template
    statement = select(Template).where(Template.id == templates[new_index])
    result = await session.execute(statement)
    template = result.scalar_one_or_none()
    
    if not template:
        await callback.answer("Шаблон не найден")
        return
    
    # Update state
    await state.update_data(current_template_index=new_index)
    
    # Update message with new template
    try:
        # Check if template has a Telegram file_id or a local path
        if template.file_id:
            # Use Telegram file ID
            photo = template.file_id
        else:
            # Use local file path - extract filename from path
            filename = template.path.split('/')[-1]
            # Use the web app base URL from settings
            photo = f"{settings.web_app_base_url}/uploads/{filename}"
        
        if callback.message:
            # Delete the previous message and send a new one with the updated template
            try:
                await callback.message.delete()
            except Exception as e:
                logger.warning(f"Could not delete template message: {e}")
            
            # Send new template message
            sent_message = await callback.message.answer_photo(
                photo=photo,
                caption=f"Шаблон {template.name}\n\n{template.description or ''}",
                reply_markup=get_template_navigation(new_index, len(templates))
            )
            # Update message ID in state
            await state.update_data(template_message_id=sent_message.message_id)
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        await callback.answer("Ошибка при обновлении шаблона")
        return
    
    await callback.answer()


@router.callback_query(F.data.startswith("template_select_"))
async def template_select(callback: CallbackQuery, state: FSMContext, session, user, bot):
    """Handle template selection."""
    logger.info(f"Template selected: {callback.data}")
    
    # Get current state data
    data = await state.get_data()
    templates = data.get("templates", [])
    current_index = data.get("current_template_index", 0)
    request_id = data.get("request_id")
    logger.info(
        "template_select state",
        extra={
            "templates_count": len(templates),
            "current_index": current_index,
            "request_id": request_id
        }
    )
    
    if not templates:
        await callback.answer("Нет шаблонов для выбора")
        return
    
    # Get selected template
    if current_index >= len(templates):
        logger.warning("template_select index out of range", extra={"current_index": current_index})
        await callback.answer("Шаблон не найден")
        return
    template_id = templates[current_index]
    statement = select(Template).where(Template.id == template_id)
    result = await session.execute(statement)
    template = result.scalar_one_or_none()
    
    if not template:
        logger.warning("template_select template missing", extra={"template_id": template_id})
        await callback.answer("Шаблон не найден")
        return
    template_name = template.name
    
    # Ensure we have a persisted request for the selected template
    request = None
    if request_id:
        statement = select(Request).where(Request.id == request_id)
        result = await session.execute(statement)
        request = result.scalar_one_or_none()
    
    if not request:
        request = await _create_request_record(
            state,
            session,
            user,
            has_license=True,
            auto_submit=True,
            selected_template_id=template_id
        )
    else:
        request.selected_template_id = template_id
        request.status = "submitted"
        request.submitted_at = datetime.utcnow()
        await session.commit()
        await session.refresh(request)
    await state.update_data(
        request_id=request.id,
        selected_template_id=template_id,
        selected_template_name=template_name
    )
    logger.info("template_select saved", extra={"request_id": request.id, "template_id": template_id})
    
    try:
        if callback.message:
            try:
                await callback.message.edit_caption(
                    caption=f"Шаблон {template.name}\n\n✅ Этот макет выбран",
                    reply_markup=None
                )
            except Exception as e:
                logger.debug(f"Could not edit template caption: {e}")
            await callback.message.answer(f"✅ Выбран шаблон: {template_name}")
        await _finalize_request_without_photos(
            state,
            callback.message.answer if callback.message else None,
            request
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await callback.answer("Ошибка при обработке запроса")
        return
    
    await callback.answer("Макет сохранен ✅", show_alert=False)


@router.message(LightVehicleStates.sending_photos, F.photo)
async def handle_photo(message: Message, state: FSMContext, session):
    """Handle photo uploads."""
    logger.info("Photo handler called")
    # Get current state data
    data = await state.get_data()
    request_id = data.get("request_id")
    photo_count = data.get("photo_count", 0)
    
    # Increment photo count
    photo_count += 1
    await state.update_data(photo_count=photo_count)
    
    # Save photo info to DB
    # TODO: Implement actual file saving
    
    if photo_count < 4:
        await message.answer(f"Получено фото {photo_count}/4")
    else:
        # All photos received
        if request_id:
            # Update request status
            statement = select(Request).where(Request.id == request_id)
            result = await session.execute(statement)
            request = result.scalar_one_or_none()
            if request:
                request.status = "submitted"
                request.submitted_at = datetime.utcnow()
                await session.commit()
        
        await message.answer(
            THANKS + f"\n\nВаша заявка: #REQ-{request_id}",
            reply_markup=get_main_menu()
        )
        await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Handle cancellation via callback."""
    logger.info("Cancel callback handler called")
    await state.clear()
    if callback.message:
        try:
            await callback.message.edit_text(
                CANCELLED,
                reply_markup=get_main_menu()
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            # If we can't edit, send a new message
            await callback.message.answer(
                CANCELLED,
                reply_markup=get_main_menu()
            )
    await callback.answer()


@router.message(F.text == "Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    """Handle cancellation."""
    logger.info("Cancel handler called")
    await state.clear()
    await message.answer(
        CANCELLED,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "back")
async def back_callback(callback: CallbackQuery, state: FSMContext):
    """Handle back navigation via callback."""
    logger.info("Back callback handler called")
    current_state = await state.get_state()
    
    if callback.message:
        try:
            if current_state == LightVehicleStates.choosing_license_option:
                await state.set_state(LightVehicleStates.choosing_license)
                await callback.message.edit_text(
                    BACK_TEXT,
                    reply_markup=get_license_yes_no_menu()
                )
            elif current_state == LightVehicleStates.choosing_no_license_option:
                await state.set_state(LightVehicleStates.choosing_license)
                await callback.message.edit_text(
                    BACK_TEXT,
                    reply_markup=get_license_yes_no_menu()
                )
            elif current_state == LightVehicleStates.entering_year:
                await state.set_state(LightVehicleStates.choosing_brand)
                await callback.message.edit_text(
                    BACK_TEXT,
                    reply_markup=get_yes_no_menu()
                )
            # For other states, just go back to main menu
            else:
                await state.clear()
                await callback.message.edit_text(
                    "Возвращаемся к началу...",
                    reply_markup=get_main_menu()
                )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            # If we can't edit, send a new message
            if current_state == LightVehicleStates.choosing_license_option:
                await state.set_state(LightVehicleStates.choosing_license)
                await callback.message.answer(
                    BACK_TEXT,
                    reply_markup=get_license_yes_no_menu()
                )
            elif current_state == LightVehicleStates.choosing_no_license_option:
                await state.set_state(LightVehicleStates.choosing_license)
                await callback.message.answer(
                    BACK_TEXT,
                    reply_markup=get_license_yes_no_menu()
                )
            elif current_state == LightVehicleStates.entering_year:
                await state.set_state(LightVehicleStates.choosing_brand)
                await callback.message.answer(
                    BACK_TEXT,
                    reply_markup=get_yes_no_menu()
                )
            # For other states, just go back to main menu
            else:
                await state.clear()
                await callback.message.answer(
                    "Возвращаемся к началу...",
                    reply_markup=get_main_menu()
                )
    await callback.answer()


@router.message(F.text == "Назад")
async def back_handler(message: Message, state: FSMContext):
    """Handle back navigation."""
    logger.info("Back handler called")
    current_state = await state.get_state()
    
    if current_state == LightVehicleStates.choosing_license_option:
        await state.set_state(LightVehicleStates.choosing_license)
        await message.answer(
            BACK_TEXT,
            reply_markup=get_license_yes_no_menu()
        )
    elif current_state == LightVehicleStates.choosing_no_license_option:
        await state.set_state(LightVehicleStates.choosing_license)
        await message.answer(
            BACK_TEXT,
            reply_markup=get_license_yes_no_menu()
        )
    elif current_state == LightVehicleStates.entering_year:
        await state.set_state(LightVehicleStates.choosing_brand)
        await message.answer(
            BACK_TEXT,
            reply_markup=get_yes_no_menu()
        )
    # For other states, just go back to main menu
    else:
        await state.clear()
        await message.answer(
            "Возвращаемся к началу...",
            reply_markup=get_main_menu()
        )
