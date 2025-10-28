"""FSM states for light vehicle requests."""

from aiogram.fsm.state import State, StatesGroup


class LightVehicleStates(StatesGroup):
    """States for light vehicle registration process."""
    
    # Initial state
    choosing_brand = State()
    
    # If user has brand
    sending_photos = State()  # Sending 4 auto photos
    
    # If user doesn't have brand
    entering_year = State()
    choosing_license = State()
    choosing_license_option = State()
    sending_photos_no_brand = State()  # Sending 4 auto photos