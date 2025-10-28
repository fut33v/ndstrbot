"""Common handlers."""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states.light import LightVehicleStates
from app.states.cargo import CargoVehicleStates

router = Router()


@router.message(F.content_type != "text")
async def invalid_content_type(message: Message, state: FSMContext):
    """Handle non-text messages during photo upload process."""
    # Check if we're in a photo upload state
    current_state = await state.get_state()
    
    # List of states where we expect photos
    photo_states = [
        LightVehicleStates.sending_photos,
        LightVehicleStates.sending_photos_no_brand,
        CargoVehicleStates.sending_auto_photos,
        CargoVehicleStates.sending_sts_photos
    ]
    
    # Only respond with the photo request message if we're in a photo upload state
    if current_state in [str(state) for state in photo_states]:
        await message.answer("Пожалуйста, пришлите фото. Допустимые форматы: JPEG/PNG.")