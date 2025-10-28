"""File upload service."""

import os
from typing import Optional
from aiogram.types import Message

from infra.config import settings


async def save_file(message: Message, chat_id: int, filename: str) -> Optional[str]:
    """
    Save file locally and return file path.
    
    Args:
        message: Telegram message with file
        chat_id: User chat ID
        filename: Filename to save as
        
    Returns:
        File path if successful, None otherwise
    """
    if settings.fake_files:
        # Fake mode - don't download files
        return None
    
    # Create user directory
    user_dir = os.path.join(settings.base_dir, settings.upload_dir, str(chat_id))
    os.makedirs(user_dir, exist_ok=True)
    
    # Get file path
    file_path = os.path.join(user_dir, filename)
    
    # Download file
    try:
        file = await message.bot.get_file(message.photo[-1].file_id)
        await message.bot.download_file(file.file_path, file_path)
        return file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        return None