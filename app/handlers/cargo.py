"""Cargo vehicle handlers."""

import logging
import os
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlmodel import select

from app.states.cargo import CargoVehicleStates
from app.keyboards.inline import get_main_menu, get_cancel_menu
from domain.models import Request, File
from infra.config import settings

# Text constants
CARGO_INTRO = """📋 Для согласования с Яндексом отправьте 4 фото чистого авто (с 4 сторон) и 2 фото СТС (с обеих сторон).

🚚 Какой автомобиль подойдёт:
⚖️ Грузоподъёмность: до 10 тонн
🏗 Кузов: каблук, тент, автофургон (будка) или цельнометаллический фургон
📦 Грузовой отсек одного из четырёх типов:

🔹 S (малый) — длиной от 170 см, шириной от 100 см, высотой от 90 см
🔹 M (средний) — длиной от 260 см, шириной от 130 см, высотой от 150 см
🔹 L (большой) — длиной от 380 см, шириной от 180 см, высотой от 180 см
🔹 XL — длиной от 400 см, шириной от 190 см, высотой от 200 см
🔹 XXL — длиной от 500 см, шириной от 200 см, высотой от 200 см"""

SEND4_AUTO = "📸 Отправьте 4 фото автомобиля: спереди, сзади, слева и справа."
SEND2_STS = "📄 Теперь отправьте 2 фото СТС (лицевая и оборотная стороны)."
THANKS = "✅ Спасибо! После согласования мы свяжемся с вами и пригласим на ближайшую дату."
INVALID_PHOTO = "⚠️ Пожалуйста, пришлите фото (JPEG/PNG)."
CANCELLED = "↩️ Заявка отменена. Чтобы начать заново — /start."

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "cargo_vehicle")
async def start_cargo_vehicle(callback: CallbackQuery, state: FSMContext, session, user):
    """Start cargo vehicle registration process."""
    logger.info(f"Cargo vehicle handler called with callback data: '{callback.data}'")
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
    if callback.message:
        try:
            await callback.message.edit_text(
                CARGO_INTRO,
                reply_markup=get_cancel_menu()
            )
            # Send a new message for photo progress and store its ID
            sent_message = await callback.message.answer("📷 Ожидание фото авто 1/4", reply_markup=get_cancel_menu())
            await state.update_data(auto_photo_progress_message_id=sent_message.message_id)
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback.answer("Ошибка при обработке запроса")
            return
    await callback.answer()


@router.message(CargoVehicleStates.sending_auto_photos, F.photo)
async def handle_auto_photo(message: Message, state: FSMContext, session, user, bot: Bot):
    """Handle auto photo uploads."""
    logger.info("Cargo auto photo handler called")
    # Get current state data
    data = await state.get_data()
    auto_photo_count = data.get("auto_photo_count", 0)
    request_id = data.get("request_id")
    
    # Increment photo count
    auto_photo_count += 1
    await state.update_data(auto_photo_count=auto_photo_count)
    
    # Get the photo with the highest resolution
    photo = message.photo[-1]
    
    # Download and save the photo
    try:
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.base_dir, "storage", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Download file from Telegram
        file = await bot.get_file(photo.file_id)
        file_extension = file.file_path.split('.')[-1] if file.file_path else 'jpg'
        
        # Create unique filename
        filename = f"request_{request_id}_auto_{auto_photo_count}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Download file
        await bot.download_file(file.file_path, file_path)
        
        # Save file info to database
        if request_id:
            file_record = File(
                request_id=request_id,
                kind="auto_photo",
                file_id=photo.file_id,
                path=f"uploads/{filename}"
            )
            session.add(file_record)
            await session.commit()
        
        logger.info(f"Auto photo saved: {filename}")
    except Exception as e:
        logger.error(f"Error saving auto photo: {e}")
    
    if auto_photo_count < 4:
        # Send a new message for each photo progress instead of updating
        await message.answer(f"📷 Получено фото авто {auto_photo_count}/4")
    else:
        # All auto photos received
        await state.set_state(CargoVehicleStates.sending_sts_photos)
        # Send the STS photo instruction message
        await message.answer(SEND2_STS, reply_markup=get_cancel_menu())


@router.message(CargoVehicleStates.sending_auto_photos, F.media_group_id)
async def handle_auto_photo_album(message: Message, state: FSMContext, session, user):
    """Handle auto photo album uploads."""
    logger.info(f"Auto photo album handler called with media_group_id: {message.media_group_id}")
    
    # Get current state data
    data = await state.get_data()
    auto_photo_count = data.get("auto_photo_count", 0)
    
    # For albums, we'll count all photos in the album
    album_size = 4  # We expect 4 photos in an album
    new_photo_count = min(auto_photo_count + album_size, 4)  # Cap at 4 photos
    await state.update_data(auto_photo_count=new_photo_count)
    
    # Save photo info to DB
    # TODO: Implement actual file saving
    
    if new_photo_count < 4:
        # Send a new message for progress instead of updating
        await message.answer(f"📷 Получено фото авто {new_photo_count}/4")
    else:
        # All auto photos received (4/4)
        await state.set_state(CargoVehicleStates.sending_sts_photos)
        # Send the STS photo instruction message
        await message.answer(SEND2_STS, reply_markup=get_cancel_menu())


@router.message(CargoVehicleStates.sending_sts_photos, F.photo)
async def handle_sts_photo(message: Message, state: FSMContext, session, user, bot: Bot):
    """Handle STS photo uploads."""
    logger.info("Cargo STS photo handler called")
    # Get current state data
    data = await state.get_data()
    sts_photo_count = data.get("sts_photo_count", 0)
    request_id = data.get("request_id")
    
    # Increment photo count
    sts_photo_count += 1
    await state.update_data(sts_photo_count=sts_photo_count)
    
    # Get the photo with the highest resolution
    photo = message.photo[-1]
    
    # Download and save the photo
    try:
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.base_dir, "storage", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Download file from Telegram
        file = await bot.get_file(photo.file_id)
        file_extension = file.file_path.split('.')[-1] if file.file_path else 'jpg'
        
        # Create unique filename
        filename = f"request_{request_id}_sts_{sts_photo_count}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Download file
        await bot.download_file(file.file_path, file_path)
        
        # Save file info to database
        if request_id:
            file_record = File(
                request_id=request_id,
                kind="sts_photo",
                file_id=photo.file_id,
                path=f"uploads/{filename}"
            )
            session.add(file_record)
            await session.commit()
        
        logger.info(f"STS photo saved: {filename}")
    except Exception as e:
        logger.error(f"Error saving STS photo: {e}")
    
    if sts_photo_count < 2:
        # Send a new message for each photo progress instead of updating
        await message.answer(f"📷 Получено фото СТС {sts_photo_count}/2")
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
        
        # Send the final success message without buttons
        await message.answer(
            THANKS + f"\n\n🆔 Ваша заявка: #REQ-{request_id}"
        )
        await state.clear()


@router.message(CargoVehicleStates.sending_sts_photos, F.media_group_id)
async def handle_sts_photo_album(message: Message, state: FSMContext, session, user):
    """Handle STS photo album uploads."""
    logger.info(f"STS photo album handler called with media_group_id: {message.media_group_id}")
    
    # Get current state data
    data = await state.get_data()
    sts_photo_count = data.get("sts_photo_count", 0)
    request_id = data.get("request_id")
    
    # For albums, we'll count all photos in the album
    album_size = 2  # We expect 2 photos in an STS album
    new_photo_count = min(sts_photo_count + album_size, 2)  # Cap at 2 photos
    await state.update_data(sts_photo_count=new_photo_count)
    
    # Save photo info to DB
    # TODO: Implement actual file saving
    
    if new_photo_count < 2:
        # Send a new message for progress instead of updating
        await message.answer(f"📷 Получено фото СТС {new_photo_count}/2")
    else:
        # All photos received (2/2)
        if request_id:
            # Update request status
            statement = select(Request).where(Request.id == request_id)
            result = await session.execute(statement)
            request = result.scalar_one_or_none()
            if request:
                request.status = "submitted"
                request.submitted_at = datetime.utcnow()
                await session.commit()
        
        # Send the final success message without buttons
        await message.answer(
            THANKS + f"\n\n🆔 Ваша заявка: #REQ-{request_id}"
        )
        await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext, session, user):
    """Handle cancellation."""
    logger.info("Cargo cancel handler called")
    await state.clear()
    if callback.message:
        try:
            await callback.message.edit_text(
                CANCELLED,
                reply_markup=get_main_menu()
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback.answer("Ошибка при обработке запроса")
            return
    await callback.answer()