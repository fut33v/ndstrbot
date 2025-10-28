"""Cargo vehicle handlers."""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlmodel import select

from app.states.cargo import CargoVehicleStates
from app.keyboards.reply import get_main_menu, get_cancel_menu
from domain.models import Request

# Text constants
CARGO_INTRO = "Для согласования с Яндексом отправьте 4 фото чистого авто (с 4 сторон) и 2 фото СТС (с обеих сторон)."
SEND4_AUTO = "Отправьте 4 фото автомобиля: спереди, сзади, слева и справа."
SEND2_STS = "Теперь отправьте 2 фото СТС (лицевая и оборотная стороны)."
THANKS = "Спасибо! После согласования мы свяжемся с вами и пригласим на ближайшую дату."
INVALID_PHOTO = "Пожалуйста, пришлите фото (JPEG/PNG)."
CANCELLED = "Заявка отменена. Чтобы начать заново — /start."

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "Грузовой")
async def start_cargo_vehicle(message: Message, state: FSMContext, session, user):
    """Start cargo vehicle registration process."""
    logger.info(f"Cargo vehicle handler called with text: '{message.text}'")
    # Create request
    request = Request(
        user_id=user.id,
        category="грузовой"
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    
    # Save request ID in state
    await state.update_data(request_id=request.id)
    
    await state.set_state(CargoVehicleStates.sending_auto_photos)
    await message.answer(
        CARGO_INTRO,
        reply_markup=get_cancel_menu()
    )
    await message.answer(
        SEND4_AUTO,
        reply_markup=get_cancel_menu()
    )


@router.message(CargoVehicleStates.sending_auto_photos, F.photo)
async def handle_auto_photo(message: Message, state: FSMContext):
    """Handle auto photo uploads."""
    logger.info("Cargo auto photo handler called")
    # Get current state data
    data = await state.get_data()
    auto_photo_count = data.get("auto_photo_count", 0)
    
    # Increment photo count
    auto_photo_count += 1
    await state.update_data(auto_photo_count=auto_photo_count)
    
    # Save photo info to DB
    # TODO: Implement actual file saving
    
    if auto_photo_count < 4:
        await message.answer(f"Получено фото авто {auto_photo_count}/4")
    else:
        # All auto photos received
        await state.set_state(CargoVehicleStates.sending_sts_photos)
        await message.answer(
            SEND2_STS,
            reply_markup=get_cancel_menu()
        )


@router.message(CargoVehicleStates.sending_sts_photos, F.photo)
async def handle_sts_photo(message: Message, state: FSMContext, session):
    """Handle STS photo uploads."""
    logger.info("Cargo STS photo handler called")
    # Get current state data
    data = await state.get_data()
    sts_photo_count = data.get("sts_photo_count", 0)
    request_id = data.get("request_id")
    
    # Increment photo count
    sts_photo_count += 1
    await state.update_data(sts_photo_count=sts_photo_count)
    
    # Save photo info to DB
    # TODO: Implement actual file saving
    
    if sts_photo_count < 2:
        await message.answer(f"Получено фото СТС {sts_photo_count}/2")
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
    logger.info("Cargo cancel handler called")
    await state.clear()
    await message.answer(
        CANCELLED,
        reply_markup=get_main_menu()
    )