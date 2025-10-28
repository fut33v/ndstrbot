"""Formatting utilities."""

import logging
from domain.models import Request


logger = logging.getLogger(__name__)


def format_request_brief(req: Request) -> str:
    """
    Format brief request information.
    
    Args:
        req: Request model instance
        
    Returns:
        Formatted request brief text
    """
    logger.debug(f"Formatting brief request info for request ID {req.id}")
    
    # Add status emojis
    status_emoji = {
        "draft": "📝",
        "submitted": "📤",
        "approved": "✅",
        "rejected": "❌"
    }
    
    emoji = status_emoji.get(req.status, "📋")
    text = f"{emoji} #{req.id} | {req.category} | {req.status}"
    
    if req.category == "легковой":
        if req.has_brand is not None:
            text += f" | Бренд: {'Да' if req.has_brand else 'Нет'}"
        if req.year:
            text += f" | {req.year}г."
        if req.has_license is not None:
            text += f" | Лицензия: {'Да' if req.has_license else 'Нет'}"
    
    text += f" | {req.created_at.strftime('%d.%m.%Y')}"
    
    return text


def format_request_details(req: Request) -> str:
    """
    Format detailed request information.
    
    Args:
        req: Request model instance
        
    Returns:
        Formatted request details text
    """
    logger.debug(f"Formatting detailed request info for request ID {req.id}")
    
    # Add status emojis
    status_emoji = {
        "draft": "📝",
        "submitted": "📤",
        "approved": "✅",
        "rejected": "❌"
    }
    
    emoji = status_emoji.get(req.status, "📋")
    text = f"{emoji} Заявка #{req.id}\n"
    text += f"📂 Категория: {req.category}\n"
    text += f"📊 Статус: {req.status}\n"
    
    if req.category == "легковой":
        if req.has_brand is not None:
            text += f"🚗 Бренд: {'Да' if req.has_brand else 'Нет'}\n"
        if req.year:
            text += f"📅 Год выпуска: {req.year}\n"
        if req.has_license is not None:
            text += f"📄 Лицензия: {'Да' if req.has_license else 'Нет'}\n"
    
    if req.submitted_at:
        text += f"⏰ Дата подачи: {req.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    # Add file information
    if req.files:
        text += f"\n📁 Файлы ({len(req.files)}):\n"
        for file in req.files:
            text += f"- {file.kind}: {file.file_id}\n"
    
    return text