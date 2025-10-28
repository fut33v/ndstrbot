"""Light vehicle handlers."""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlmodel import select

from app.states.light import LightVehicleStates
from app.keyboards.reply import get_main_menu, get_yes_no_menu, get_cancel_menu, get_back_cancel_menu
from app.keyboards.inline import get_license_options
from app.services.validators import validate_year
from domain.models import Request

# Text constants
BRAND_Q = "Есть ли сейчас у вас бренд?"
SEND4_AUTO = "Отправьте 4 фото автомобиля: спереди, сзади, слева и справа."
YEAR_Q = "Укажите год выпуска вашего авто (1980–{current_year})."
LICENSE_Q = "Есть ли лицензия?"
OPTIONS_TEXT = "Варианты: оклейка, переклейка и платной оклейки."
LICENSE_WRAP = "Оклейка для получения лицензии."
THANKS = "Спасибо! Мы свяжемся с вами и пригласим на ближайшую дату."
INVALID_PHOTO = "Пожалуйста, пришлите фото (JPEG/PNG)."
CANCELLED = "Заявка отменена. Чтобы начать заново — /start."
BACK_TEXT = "Шаг назад. Продолжим."

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "Легковой")
async def start_light_vehicle(message: Message, state: FSMContext):
    """Start light vehicle registration process."""
    logger.info(f"Light vehicle handler called with text: '{message.text}'")
    await state.set_state(LightVehicleStates.choosing_brand)
    await message.answer(
        BRAND_Q,
        reply_markup=get_yes_no_menu()
    )


@router.message(LightVehicleStates.choosing_brand, F.text == "Да")
async def brand_yes(message: Message, state: FSMContext, session, user):
    """Handle 'Yes' to brand question."""
    logger.info("Brand yes handler called")
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
    await message.answer(
        SEND4_AUTO,
        reply_markup=get_cancel_menu()
    )


@router.message(LightVehicleStates.choosing_brand, F.text == "Нет")
async def brand_no(message: Message, state: FSMContext):
    """Handle 'No' to brand question."""
    logger.info("Brand no handler called")
    await state.update_data(has_brand=False)
    await state.set_state(LightVehicleStates.entering_year)
    await message.answer(
        YEAR_Q.format(current_year=2025),  # TODO: Use actual current year
        reply_markup=get_cancel_menu()
    )


@router.message(LightVehicleStates.entering_year)
async def enter_year(message: Message, state: FSMContext):
    """Handle year input."""
    logger.info("Enter year handler called")
    is_valid, year = validate_year(message.text)
    
    if not is_valid:
        await message.answer("Пожалуйста, введите корректный год (1980-2025)")
        return
    
    await state.update_data(year=year)
    await state.set_state(LightVehicleStates.choosing_license)
    await message.answer(
        LICENSE_Q,
        reply_markup=get_yes_no_menu()
    )


@router.message(LightVehicleStates.choosing_license, F.text == "Да")
async def license_yes(message: Message, state: FSMContext):
    """Handle 'Yes' to license question."""
    logger.info("License yes handler called")
    await state.update_data(has_license=True)
    await state.set_state(LightVehicleStates.choosing_license_option)
    await message.answer(
        OPTIONS_TEXT,
        reply_markup=get_license_options()
    )


@router.message(LightVehicleStates.choosing_license, F.text == "Нет")
async def license_no(message: Message, state: FSMContext, session, user):
    """Handle 'No' to license question."""
    logger.info("License no handler called")
    await state.update_data(has_license=False)
    
    # Create request
    request = Request(
        user_id=user.id,
        category="легковой",
        has_brand=False,
        has_license=False
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    
    # Save request ID in state
    await state.update_data(request_id=request.id)
    
    await message.answer(LICENSE_WRAP)
    await state.set_state(LightVehicleStates.sending_photos_no_brand)
    await message.answer(
        SEND4_AUTO,
        reply_markup=get_cancel_menu()
    )


@router.callback_query(F.data.in_(["wrap", "re_wrap", "paid_wrap"]))
async def license_option_selected(callback: CallbackQuery, state: FSMContext, session, user):
    """Handle license option selection."""
    logger.info(f"License option selected: {callback.data}")
    # Create request
    request = Request(
        user_id=user.id,
        category="легковой",
        has_brand=False,
        has_license=True
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    
    # Save request ID in state
    await state.update_data(request_id=request.id)
    
    await callback.message.edit_text("Выбрано: " + callback.data)
    await state.set_state(LightVehicleStates.sending_photos_no_brand)
    await callback.message.answer(
        SEND4_AUTO,
        reply_markup=get_cancel_menu()
    )
    await callback.answer()


@router.message(LightVehicleStates.sending_photos, F.photo)
@router.message(LightVehicleStates.sending_photos_no_brand, F.photo)
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


@router.message(F.text == "Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    """Handle cancellation."""
    logger.info("Cancel handler called")
    await state.clear()
    await message.answer(
        CANCELLED,
        reply_markup=get_main_menu()
    )


@router.message(F.text == "Назад")
async def back_handler(message: Message, state: FSMContext):
    """Handle back navigation."""
    logger.info("Back handler called")
    current_state = await state.get_state()
    
    if current_state == LightVehicleStates.choosing_license_option:
        await state.set_state(LightVehicleStates.choosing_license)
        await message.answer(
            BACK_TEXT,
            reply_markup=get_yes_no_menu()
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