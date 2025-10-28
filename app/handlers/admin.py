"""Admin handlers."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlmodel import select
from sqlalchemy.orm import selectinload

from infra.config import settings
from domain.models import Request, User, Admin
from app.utils.formatters import format_request_details


logger = logging.getLogger(__name__)

router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin (both from config and database)."""
    # Check if user is in config admin_ids
    if user_id in settings.admin_ids:
        return True
    
    return False


async def is_admin_db(session, user_id: int) -> bool:
    """Check if user is admin in database."""
    statement = select(Admin).where(Admin.tg_id == user_id)
    result = await session.execute(statement)
    admin = result.scalar_one_or_none()
    return admin is not None


async def is_admin_combined(session, user_id: int) -> bool:
    """Check if user is admin (both from config and database)."""
    # Check if user is in config admin_ids
    if user_id in settings.admin_ids:
        return True
    
    # Check if user is in database admins
    return await is_admin_db(session, user_id)


# Update all the command filters to use a custom filter instead of the built-in one
@router.message(Command("admin"))
async def admin_handler(message: Message, session):
    """Handle /admin command."""
    if not await is_admin_combined(session, message.from_user.id):
        await message.answer("🚫 Недостаточно прав")
        return
        
    logger.info(f"Admin handler called by user {message.from_user.id}")
    try:
        await message.answer(
            "🔐 Админ панель:\n"
            "📊 /stats - статистика заявок\n"
            "🔍 /find <tg_id|req_id> - найти заявку\n"
            "✅ /approve <req_id> - одобрить заявку\n"
            "❌ /reject <req_id> - отклонить заявку\n"
            "➕ /addadmin <tg_id|username> - добавить админа\n"
            "➖ /deladmin <tg_id|username> - удалить админа\n"
            "📋 /listadmins - список админов"
        )
        logger.debug("Admin handler completed successfully")
    except Exception as e:
        logger.error(f"Error in admin handler: {e}", exc_info=True)
        raise


@router.message(Command("addadmin"))
async def add_admin_handler(message: Message, session):
    """Handle /addadmin command."""
    if not await is_admin_combined(session, message.from_user.id):
        await message.answer("🚫 Недостаточно прав")
        return
        
    logger.info(f"Add admin handler called by user {message.from_user.id}")
    try:
        # Parse argument
        args = message.text.split()
        if len(args) < 2:
            await message.answer("ℹ️ Использование: /addadmin <tg_id|username>")
            return
        
        identifier = args[1]
        
        # Check if admin already exists in config
        if identifier.isdigit() and int(identifier) in settings.admin_ids:
            await message.answer("⚠️ Этот пользователь уже является админом (в конфигурации)")
            return
        
        # Check if admin already exists in database
        if identifier.isdigit():
            statement = select(Admin).where(Admin.tg_id == int(identifier))
        else:
            statement = select(Admin).where(Admin.username == identifier)
        
        result = await session.execute(statement)
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            await message.answer("⚠️ Этот пользователь уже является админом (в базе данных)")
            return
        
        # Create new admin record
        new_admin = Admin(
            tg_id=int(identifier) if identifier.isdigit() else None,
            username=identifier if not identifier.isdigit() else None,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            added_by=message.from_user.id
        )
        
        session.add(new_admin)
        await session.commit()
        await session.refresh(new_admin)
        
        await message.answer(f"✅ Админ успешно добавлен (ID: {new_admin.id})")
        logger.info(f"Admin {message.from_user.id} added new admin: {identifier}")
    except Exception as e:
        logger.error(f"Error in add admin handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при добавлении админа: {e}")


@router.message(Command("deladmin"))
async def del_admin_handler(message: Message, session):
    """Handle /deladmin command."""
    if not await is_admin_combined(session, message.from_user.id):
        await message.answer("🚫 Недостаточно прав")
        return
        
    logger.info(f"Delete admin handler called by user {message.from_user.id}")
    try:
        # Parse argument
        args = message.text.split()
        if len(args) < 2:
            await message.answer("ℹ️ Использование: /deladmin <tg_id|username>")
            return
        
        identifier = args[1]
        
        # Check if admin exists in config (can't delete config admins)
        if identifier.isdigit() and int(identifier) in settings.admin_ids:
            await message.answer("⚠️ Этот админ задан в конфигурации и не может быть удален через команду")
            return
        
        # Find and delete admin from database
        if identifier.isdigit():
            statement = select(Admin).where(Admin.tg_id == int(identifier))
        else:
            statement = select(Admin).where(Admin.username == identifier)
        
        result = await session.execute(statement)
        admin = result.scalar_one_or_none()
        
        if not admin:
            await message.answer("🔍 Админ не найден в базе данных")
            return
        
        await session.delete(admin)
        await session.commit()
        
        await message.answer(f"✅ Админ успешно удален")
        logger.info(f"Admin {message.from_user.id} deleted admin: {identifier}")
    except Exception as e:
        logger.error(f"Error in delete admin handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при удалении админа: {e}")


@router.message(Command("listadmins"))
async def list_admins_handler(message: Message, session):
    """Handle /listadmins command."""
    if not await is_admin_combined(session, message.from_user.id):
        await message.answer("🚫 Недостаточно прав")
        return
        
    logger.info(f"List admins handler called by user {message.from_user.id}")
    try:
        # Get config admins
        config_admins = [str(id) for id in settings.admin_ids]
        config_admins_text = ", ".join(config_admins) if config_admins else "Нет"
        
        # Get database admins
        statement = select(Admin)
        result = await session.execute(statement)
        db_admins = result.scalars().all()
        
        db_admins_text = "\n".join([
            f"- {admin.tg_id or admin.username} (добавлен {admin.added_at.strftime('%d.%m.%Y')})" 
            for admin in db_admins
        ]) if db_admins else "Нет"
        
        text = f"🔐 Админы из конфигурации:\n{config_admins_text}\n\n📋 Админы из базы данных:\n{db_admins_text}"
        await message.answer(text)
    except Exception as e:
        logger.error(f"Error in list admins handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка при получении списка админов: {e}")


@router.message(Command("stats"))
async def stats_handler(message: Message, session):
    """Handle /stats command."""
    if not await is_admin_combined(session, message.from_user.id):
        await message.answer("🚫 Недостаточно прав")
        return
        
    logger.info(f"Stats handler called by user {message.from_user.id}")
    try:
        # Get total requests count
        logger.debug("Fetching all requests for stats")
        statement = select(Request)
        result = await session.execute(statement)
        all_requests = result.scalars().all()
        logger.debug(f"Found {len(all_requests)} requests")
        
        # Count by status
        status_counts = {}
        for req in all_requests:
            status_counts[req.status] = status_counts.get(req.status, 0) + 1
        
        # Format response
        text = "📊 Статистика заявок:\n"
        for status, count in status_counts.items():
            text += f"{status}: {count}\n"
        
        await message.answer(text)
        logger.debug("Stats handler completed successfully")
    except Exception as e:
        logger.error(f"Error in stats handler: {e}", exc_info=True)
        raise


@router.message(Command("find"))
async def find_handler(message: Message, session):
    """Handle /find command."""
    if not await is_admin_combined(session, message.from_user.id):
        await message.answer("🚫 Недостаточно прав")
        return
        
    logger.info(f"Find handler called by user {message.from_user.id}")
    try:
        # Parse argument
        args = message.text.split()
        if len(args) < 2:
            await message.answer("ℹ️ Использование: /find <tg_id|req_id>")
            return
        
        identifier = args[1]
        
        # Try to find by request ID first
        if identifier.isdigit():
            req_id = int(identifier)
            # Eagerly load files relationship to avoid lazy loading issues
            statement = select(Request).where(Request.id == req_id).options(selectinload(Request.files))
            result = await session.execute(statement)
            request = result.scalar_one_or_none()
            
            if request:
                text = format_request_details(request)
                await message.answer(text)
                return
        
        # Try to find by TG ID
        if identifier.isdigit():
            tg_id = int(identifier)
            # Find user first
            user_statement = select(User).where(User.tg_id == tg_id)
            user_result = await session.execute(user_statement)
            user = user_result.scalar_one_or_none()
            
            if user:
                # Get user's requests with eagerly loaded files
                req_statement = select(Request).where(Request.user_id == user.id).options(selectinload(Request.files))
                req_result = await session.execute(req_statement)
                requests = req_result.scalars().all()
                
                if requests:
                    text = "📋 Заявки пользователя:\n\n"
                    for req in requests:
                        text += format_request_details(req) + "\n\n"
                    await message.answer(text)
                else:
                    await message.answer("📭 У пользователя нет заявок")
            else:
                await message.answer("🔍 Пользователь не найден")
        else:
            await message.answer("⚠️ Неверный формат ID")
    except Exception as e:
        logger.error(f"Error in find handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("approve"))
async def approve_handler(message: Message, session):
    """Handle /approve command."""
    if not await is_admin_combined(session, message.from_user.id):
        await message.answer("🚫 Недостаточно прав")
        return
        
    logger.info(f"Approve handler called by user {message.from_user.id}")
    try:
        # Parse argument
        args = message.text.split()
        if len(args) < 2:
            await message.answer("ℹ️ Использование: /approve <req_id>")
            return
        
        req_id = int(args[1])
        
        # Find request with eagerly loaded files
        statement = select(Request).where(Request.id == req_id).options(selectinload(Request.files))
        result = await session.execute(statement)
        request = result.scalar_one_or_none()
        
        if not request:
            await message.answer("🔍 Заявка не найдена")
            return
        
        # Update status
        request.status = "approved"
        await session.commit()
        
        await message.answer(f"✅ Заявка #{req_id} одобрена")
    except Exception as e:
        logger.error(f"Error in approve handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("reject"))
async def reject_handler(message: Message, session):
    """Handle /reject command."""
    if not await is_admin_combined(session, message.from_user.id):
        await message.answer("🚫 Недостаточно прав")
        return
        
    logger.info(f"Reject handler called by user {message.from_user.id}")
    try:
        # Parse argument
        args = message.text.split()
        if len(args) < 2:
            await message.answer("ℹ️ Использование: /reject <req_id>")
            return
        
        req_id = int(args[1])
        
        # Find request with eagerly loaded files
        statement = select(Request).where(Request.id == req_id).options(selectinload(Request.files))
        result = await session.execute(statement)
        request = result.scalar_one_or_none()
        
        if not request:
            await message.answer("🔍 Заявка не найдена")
            return
        
        # Update status
        request.status = "rejected"
        await session.commit()
        
        await message.answer(f"❌ Заявка #{req_id} отклонена")
    except Exception as e:
        logger.error(f"Error in reject handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data.startswith("approve_"))
async def approve_callback(callback: CallbackQuery, session):
    """Handle approve callback."""
    if not await is_admin_combined(session, callback.from_user.id):
        await callback.answer("🚫 Недостаточно прав")
        return
    
    try:
        req_id = int(callback.data.split("_")[1])
        
        # Find request with eagerly loaded files
        statement = select(Request).where(Request.id == req_id).options(selectinload(Request.files))
        result = await session.execute(statement)
        request = result.scalar_one_or_none()
        
        if not request:
            await callback.answer("🔍 Заявка не найдена")
            return
        
        # Update status
        request.status = "approved"
        await session.commit()
        
        await callback.answer("✅ Заявка одобрена")
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Одобрена",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Error in approve callback: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data.startswith("reject_"))
async def reject_callback(callback: CallbackQuery, session):
    """Handle reject callback."""
    if not await is_admin_combined(session, callback.from_user.id):
        await callback.answer("🚫 Недостаточно прав")
        return
    
    try:
        req_id = int(callback.data.split("_")[1])
        
        # Find request with eagerly loaded files
        statement = select(Request).where(Request.id == req_id).options(selectinload(Request.files))
        result = await session.execute(statement)
        request = result.scalar_one_or_none()
        
        if not request:
            await callback.answer("🔍 Заявка не найдена")
            return
        
        # Update status
        request.status = "rejected"
        await session.commit()
        
        await callback.answer("❌ Заявка отклонена")
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ Отклонена",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Error in reject callback: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка: {e}")