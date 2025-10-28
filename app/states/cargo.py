"""FSM states for cargo vehicle requests."""

from aiogram.fsm.state import State, StatesGroup


class CargoVehicleStates(StatesGroup):
    """States for cargo vehicle registration process."""
    
    # Initial state - sending auto photos
    sending_auto_photos = State()  # Sending 4 auto photos
    
    # Sending STS photos
    sending_sts_photos = State()  # Sending 2 STS photos