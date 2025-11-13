"""Main web application module for displaying database content."""

import logging
import os
import hashlib
import hmac
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Depends, Cookie, Body, UploadFile, File as FastAPIFile, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from infra.db import get_session
from domain.models import User, Admin, Request, File, Audit, Template
from domain.schemas import RequestResponse
from infra.config import settings
from app.webapp.templates import generate_table_html, format_datetime
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Yandex GO Car Registration Bot - Admin Panel",
    description="Web interface for viewing database content",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for auth
class TelegramAuthData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str

class AdminCreate(BaseModel):
    user_id: int | None = None
    tg_id: int | None = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


def verify_telegram_auth(auth_data: dict, bot_token: str) -> bool:
    """Verify Telegram auth data using bot token."""
    check_hash = auth_data.pop('hash', None)
    if not check_hash:
        return False
    
    data_check_arr = []
    for key, value in sorted(auth_data.items()):
        if value is not None:
            data_check_arr.append(f"{key}={value}")
    
    data_check_string = '\n'.join(data_check_arr)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    return hmac_hash == check_hash


async def check_admin_access(tg_id: int) -> bool:
    """Check if user is admin via DB or env-configured IDs."""
    if tg_id in settings.admin_ids:
        return True
    async with get_session() as session:
        statement = select(Admin).where(Admin.tg_id == tg_id)
        result = await session.execute(statement)
        admin = result.scalar_one_or_none()
        return admin is not None


async def ensure_admin_record(tg_id: int, profile: Optional[Dict[str, Optional[str]]] = None) -> Optional[Admin]:
    """Make sure an Admin row exists (and is up to date) for the given tg_id."""
    async with get_session() as session:
        statement = select(Admin).where(Admin.tg_id == tg_id)
        result = await session.execute(statement)
        admin = result.scalar_one_or_none()
        if admin:
            updated = False
            if profile:
                for field in ("username", "first_name", "last_name"):
                    value = profile.get(field)
                    if value and getattr(admin, field) != value:
                        setattr(admin, field, value)
                        updated = True
            if updated:
                await session.commit()
            return admin
        if tg_id not in settings.admin_ids:
            return None
        admin = Admin(
            tg_id=tg_id,
            username=(profile or {}).get("username"),
            first_name=(profile or {}).get("first_name"),
            last_name=(profile or {}).get("last_name"),
            added_by=None,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin


def resolve_template_local_path(template: Template) -> Optional[str]:
    """Return absolute path to a template file if it exists locally."""
    if not template.path:
        return None
    candidate = template.path
    if not os.path.isabs(candidate):
        candidate = os.path.join(settings.base_dir, candidate.lstrip("./"))
    if os.path.exists(candidate):
        return candidate
    return None


@app.post("/auth/telegram")
async def telegram_auth(auth_data: TelegramAuthData):
    """Authenticate user via Telegram."""
    try:
        # Convert to dict for verification
        auth_dict = auth_data.model_dump(exclude_none=True)
        
        # Verify auth data
        if not verify_telegram_auth(auth_dict, settings.bot_token):
            raise HTTPException(status_code=401, detail="Неверные данные авторизации")
        
        # Check if user is admin
        is_admin = await check_admin_access(auth_data.id)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Доступ запрещен. Требуются права администратора.")
        await ensure_admin_record(
            auth_data.id,
            {
                "username": auth_data.username,
                "first_name": auth_data.first_name,
                "last_name": auth_data.last_name,
            }
        )
        
        # Return success with user data
        response = JSONResponse({
            "success": True,
            "user": {
                "id": auth_data.id,
                "first_name": auth_data.first_name,
                "last_name": auth_data.last_name,
                "username": auth_data.username,
                "photo_url": auth_data.photo_url
            }
        })
        
        # Set cookie with user ID
        response.set_cookie(
            key="tg_user_id",
            value=str(auth_data.id),
            httponly=True,
            max_age=30*24*60*60,  # 30 days
            samesite="lax"
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Telegram auth: {e}")
        raise HTTPException(status_code=500, detail="Ошибка авторизации")


@app.get("/auth/me")
async def get_current_user(tg_user_id: Optional[str] = Cookie(None)):
    """Get current authenticated user."""
    if not tg_user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    try:
        tg_id = int(tg_user_id)
        is_admin = await check_admin_access(tg_id)
        
        if not is_admin:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Get admin info
        async with get_session() as session:
            statement = select(Admin).where(Admin.tg_id == tg_id)
            result = await session.execute(statement)
            admin = result.scalar_one_or_none()
            if admin:
                return {
                    "id": admin.tg_id,
                    "username": admin.username,
                    "first_name": admin.first_name,
                    "last_name": admin.last_name
                }
        # No DB record but allowed via settings – create a placeholder
        admin = await ensure_admin_record(tg_id)
        if admin:
            return {
                "id": admin.tg_id,
                "username": admin.username,
                "first_name": admin.first_name,
                "last_name": admin.last_name
            }
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения информации о пользователе")


@app.post("/auth/logout")
async def logout():
    """Logout current user."""
    response = JSONResponse({"success": True})
    response.delete_cookie("tg_user_id")
    return response


@app.get("/config")
async def get_config():
    """Get public configuration."""
    return {
        "bot_username": settings.bot_username
    }

@app.get("/")
async def read_root():
    """Root endpoint with basic information and links to other endpoints."""
    return {
        "message": "Yandex GO Car Registration Bot - Admin Panel",
        "endpoints": {
            "users": "/users",
            "admins": "/admins",
            "requests": "/requests",
            "files": "/files",
            "audit": "/audit",
            "dashboard": "/dashboard"
        }
    }

@app.get("/users", response_model=List[User])
@app.get("/users/json", response_model=List[User])
async def get_users_json():
    """Get all users from the database (JSON format)."""
    try:
        async with get_session() as session:
            statement = select(User)
            result = await session.execute(statement)
            users = result.scalars().all()
            return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Error fetching users")

@app.get("/users/html", response_class=HTMLResponse)
async def get_users_html():
    """Get all users from the database (HTML format)."""
    try:
        async with get_session() as session:
            statement = select(User)
            result = await session.execute(statement)
            users = result.scalars().all()
            
            headers = ["ID", "Telegram ID", "Username", "First Name", "Last Name", "Created At", "Last Seen"]
            rows = []
            for user in users:
                rows.append([
                    user.id,
                    user.tg_id,
                    user.username or "",
                    user.first_name or "",
                    user.last_name or "",
                    format_datetime(user.created_at),
                    format_datetime(user.last_seen)
                ])
            
            html = generate_table_html("Users", headers, rows)
            return HTMLResponse(content=html, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return HTMLResponse(content=f"<h1>Error fetching users: {e}</h1>", status_code=500)

@app.post("/admins")
async def create_admin(payload: AdminCreate, tg_user_id: Optional[str] = Cookie(None)):
    """Create a new admin. Only existing admins can add others."""
    # Auth check
    if not tg_user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    try:
        requester_tg_id = int(tg_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    if not await check_admin_access(requester_tg_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Resolve user info
    async with get_session() as session:
        user_tg_id = payload.tg_id
        username = payload.username
        first_name = payload.first_name
        last_name = payload.last_name

        if payload.user_id is not None:
            stmt = select(User).where(User.id == payload.user_id)
            res = await session.execute(stmt)
            u = res.scalar_one_or_none()
            if not u:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            user_tg_id = u.tg_id
            username = u.username
            first_name = u.first_name
            last_name = u.last_name

        if not user_tg_id:
            raise HTTPException(status_code=400, detail="Отсутствует tg_id пользователя")

        # Check already admin
        stmt = select(Admin).where(Admin.tg_id == user_tg_id)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return {"success": True, "message": "Пользователь уже администратор"}

        # Create admin
        new_admin = Admin(
            tg_id=user_tg_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            added_by=requester_tg_id
        )
        session.add(new_admin)
        await session.commit()
        return {"success": True}


@app.get("/admins", response_model=List[Admin])
@app.get("/admins/json", response_model=List[Admin])
async def get_admins_json():
    """Get all admins from the database (JSON format)."""
    try:
        async with get_session() as session:
            statement = select(Admin)
            result = await session.execute(statement)
            admins = result.scalars().all()
            return admins
    except Exception as e:
        logger.error(f"Error fetching admins: {e}")
        raise HTTPException(status_code=500, detail="Error fetching admins")


@app.get("/admins/html", response_class=HTMLResponse)
async def get_admins_html():
    """Get all admins from the database (HTML format)."""
    try:
        async with get_session() as session:
            statement = select(Admin)
            result = await session.execute(statement)
            admins = result.scalars().all()
            
            headers = ["ID", "Telegram ID", "Username", "First Name", "Last Name", "Added At", "Added By"]
            rows = []
            for admin in admins:
                rows.append([
                    admin.id,
                    admin.tg_id or "",
                    admin.username or "",
                    admin.first_name or "",
                    admin.last_name or "",
                    format_datetime(admin.added_at),
                    admin.added_by or ""
                ])
            
            html = generate_table_html("Admins", headers, rows)
            return HTMLResponse(content=html, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching admins: {e}")
        return HTMLResponse(content=f"<h1>Error fetching admins: {e}</h1>", status_code=500)

@app.get("/requests", response_model=List[RequestResponse])
@app.get("/requests/json", response_model=List[RequestResponse])
async def get_requests_json():
    """Get all requests from the database (JSON format)."""
    try:
        async with get_session() as session:
            statement = select(Request, User.username).join(User, Request.user_id == User.id, isouter=True)
            result = await session.execute(statement)
            rows = result.all()
            responses = []
            for request, username in rows:
                data = RequestResponse.model_validate(request).model_dump()
                data["username"] = username
                responses.append(data)
            return responses
    except Exception as e:
        logger.error(f"Error fetching requests: {e}")
        raise HTTPException(status_code=500, detail="Error fetching requests")

@app.get("/requests/html", response_class=HTMLResponse)
async def get_requests_html():
    """Get all requests from the database (HTML format)."""
    try:
        async with get_session() as session:
            statement = select(Request)
            result = await session.execute(select(Request, User.username).join(User, Request.user_id == User.id, isouter=True))
            request_rows = result.all()
            
            headers = ["ID", "User ID", "Username", "Category", "Status", "Brand", "Year", "License", "Created At", "Submitted At"]
            rows = []
            for request, username in request_rows:
                rows.append([
                    request.id,
                    request.user_id,
                    username or "",
                    request.category,
                    request.status,
                    "Yes" if request.has_brand else "No" if request.has_brand is not None else "",
                    request.year or "",
                    "Yes" if request.has_license else "No" if request.has_license is not None else "",
                    format_datetime(request.created_at),
                    format_datetime(request.submitted_at) if request.submitted_at else ""
                ])
            
            html = generate_table_html("Requests", headers, rows)
            return HTMLResponse(content=html, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching requests: {e}")
        return HTMLResponse(content=f"<h1>Error fetching requests: {e}</h1>", status_code=500)

@app.get("/requests/{request_id}", response_model=RequestResponse)
async def get_request_by_id(request_id: int):
    """Get a single request by ID (JSON format)."""
    try:
        async with get_session() as session:
            statement = select(Request, User.username).join(User, Request.user_id == User.id, isouter=True).where(Request.id == request_id)
            result = await session.execute(statement)
            row = result.first()
            if not row:
                raise HTTPException(status_code=404, detail="Request not found")
            request, username = row
            
            data = RequestResponse.model_validate(request).model_dump()
            data["username"] = username
            return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching request {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching request")

@app.get("/requests/{request_id}/files", response_model=List[File])
async def get_files_by_request_id(request_id: int):
    """Get all files for a specific request (JSON format)."""
    try:
        async with get_session() as session:
            statement = select(File).where(File.request_id == request_id)
            result = await session.execute(statement)
            files = result.scalars().all()
            return files
    except Exception as e:
        logger.error(f"Error fetching files for request {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching files")

@app.get("/uploads/{filename}")
async def get_upload_file(filename: str):
    """Serve uploaded files."""
    try:
        # Construct file path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        file_path = os.path.join(base_dir, "storage", "uploads", filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file
        return FileResponse(file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error serving file")


@app.get("/templates/{template_id}/preview")
async def get_template_preview(template_id: int):
    """Return an image preview for the given template."""
    try:
        async with get_session() as session:
            statement = select(Template).where(Template.id == template_id)
            result = await session.execute(statement)
            template = result.scalar_one_or_none()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
        local_path = resolve_template_local_path(template)
        if local_path:
            return FileResponse(local_path)
        if template.file_id:
            async with httpx.AsyncClient(timeout=20) as client:
                tg_resp = await client.get(
                    f"https://api.telegram.org/bot{settings.bot_token}/getFile",
                    params={"file_id": template.file_id}
                )
                tg_resp.raise_for_status()
                payload = tg_resp.json()
                if not payload.get("ok"):
                    raise HTTPException(status_code=502, detail="Telegram response error")
                file_path = payload["result"].get("file_path")
                if not file_path:
                    raise HTTPException(status_code=404, detail="Telegram file missing")
                file_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file_path}"
                file_resp = await client.get(file_url)
                file_resp.raise_for_status()
                media_type = file_resp.headers.get("content-type", "image/jpeg")
                return StreamingResponse(file_resp.aiter_bytes(), media_type=media_type)
        raise HTTPException(status_code=404, detail="Template preview unavailable")
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        logger.error(f"Telegram preview fetch error: {exc}")
        raise HTTPException(status_code=502, detail="Ошибка загрузки превью из Telegram")
    except Exception as e:
        logger.error(f"Error serving template preview {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Error serving template preview")

@app.get("/files", response_model=List[File])
@app.get("/files/json", response_model=List[File])
async def get_files_json():
    """Get all files from the database (JSON format)."""
    try:
        async with get_session() as session:
            statement = select(File)
            result = await session.execute(statement)
            files = result.scalars().all()
            return files
    except Exception as e:
        logger.error(f"Error fetching files: {e}")
        raise HTTPException(status_code=500, detail="Error fetching files")

@app.get("/files/html", response_class=HTMLResponse)
async def get_files_html():
    """Get all files from the database (HTML format)."""
    try:
        async with get_session() as session:
            statement = select(File)
            result = await session.execute(statement)
            files = result.scalars().all()
            
            headers = ["ID", "Request ID", "Kind", "File ID", "Path", "Created At"]
            rows = []
            for file in files:
                rows.append([
                    file.id,
                    file.request_id,
                    file.kind,
                    file.file_id,
                    file.path,
                    format_datetime(file.created_at)
                ])
            
            html = generate_table_html("Files", headers, rows)
            return HTMLResponse(content=html, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching files: {e}")
        return HTMLResponse(content=f"<h1>Error fetching files: {e}</h1>", status_code=500)

@app.get("/audit", response_model=List[Audit])
@app.get("/audit/json", response_model=List[Audit])
async def get_audit_logs_json():
    """Get all audit logs from the database (JSON format)."""
    try:
        async with get_session() as session:
            statement = select(Audit)
            result = await session.execute(statement)
            audit_logs = result.scalars().all()
            return audit_logs
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching audit logs")

@app.get("/audit/html", response_class=HTMLResponse)
async def get_audit_logs_html():
    """Get all audit logs from the database (HTML format)."""
    try:
        async with get_session() as session:
            statement = select(Audit)
            result = await session.execute(statement)
            audit_logs = result.scalars().all()
            
            headers = ["ID", "Event", "Payload", "Created At"]
            rows = []
            for log in audit_logs:
                # Truncate payload for display
                payload = log.payload[:100] + "..." if len(log.payload) > 100 else log.payload
                rows.append([
                    log.id,
                    log.event,
                    payload,
                    format_datetime(log.created_at)
                ])
            
            html = generate_table_html("Audit Logs", headers, rows)
            return HTMLResponse(content=html, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        return HTMLResponse(content=f"<h1>Error fetching audit logs: {e}</h1>", status_code=500)

@app.get("/templates", response_model=List[Template])
@app.get("/templates/json", response_model=List[Template])
async def get_templates_json():
    """Get all templates from the database (JSON format)."""
    try:
        async with get_session() as session:
            statement = select(Template)
            result = await session.execute(statement)
            templates = result.scalars().all()
            return templates
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail="Error fetching templates")


@app.get("/templates/{template_id}", response_model=Template)
async def get_template_by_id(template_id: int):
    """Get single template by ID."""
    try:
        async with get_session() as session:
            statement = select(Template).where(Template.id == template_id)
            result = await session.execute(statement)
            template = result.scalar_one_or_none()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching template")


@app.get("/templates/html", response_class=HTMLResponse)
async def get_templates_html():
    """Get all templates from the database (HTML format)."""
    try:
        async with get_session() as session:
            statement = select(Template)
            result = await session.execute(statement)
            templates = result.scalars().all()
            
            headers = ["ID", "Название", "Описание", "Предпросмотр", "Источник", "Создан", "Создал"]
            rows = []
            for template in templates:
                preview_url = f"/templates/{template.id}/preview"
                preview_html = (
                    f'<a href="{preview_url}" target="_blank">'
                    f'<img src="{preview_url}" alt="{template.name}" '
                    f'style="max-width:180px;max-height:120px;border-radius:6px;object-fit:cover;border:1px solid #ddd;" />'
                    "</a>"
                )
                if template.path:
                    source_text = template.path
                elif template.file_id:
                    source_text = template.file_id
                else:
                    source_text = "—"
                rows.append([
                    template.id,
                    template.name,
                    template.description or "",
                    preview_html,
                    source_text,
                    format_datetime(template.created_at),
                    template.created_by or ""
                ])

            html = generate_table_html("Устаревшие макеты", headers, rows)
            return HTMLResponse(content=html, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        return HTMLResponse(content=f"<h1>Error fetching templates: {e}</h1>", status_code=500)


@app.post("/templates/upload")
async def upload_template(
    name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = FastAPIFile(...),
    tg_user_id: Optional[str] = Cookie(None)
):
    """Upload a new template image. Only admins can upload templates."""
    # Auth check
    if not tg_user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    try:
        requester_tg_id = int(tg_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    if not await check_admin_access(requester_tg_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.base_dir, "storage", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    import uuid
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"template_{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file locally first
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Upload file to Telegram and get file_id
    file_id = ""
    try:
        # Try to import aiogram - it might not be available in web app
        from aiogram import Bot
        from aiogram.types import FSInputFile
        
        bot = Bot(token=settings.bot_token)
        
        # Upload file to Telegram
        photo = FSInputFile(file_path)
        sent_message = await bot.send_photo(chat_id=requester_tg_id, photo=photo)
        file_id = sent_message.photo[-1].file_id  # Get the largest photo size file_id
            
        await bot.session.close()
    except ImportError:
        logger.info("aiogram not available in web app, skipping Telegram upload")
    except Exception as e:
        logger.error(f"Error uploading file to Telegram: {e}")
        # If Telegram upload fails, we'll still save the template with local path only
    
    # Create template record
    async with get_session() as session:
        template = Template(
            name=name,
            description=description,
            file_id=file_id,  # Store Telegram file_id if available
            path=f"uploads/{filename}",
            created_by=requester_tg_id
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template


@app.delete("/templates/{template_id}")
async def delete_template(template_id: int, tg_user_id: Optional[str] = Cookie(None)):
    """Delete a template (only for admins)."""
    if not tg_user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    try:
        requester_tg_id = int(tg_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    if not await check_admin_access(requester_tg_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    try:
        async with get_session() as session:
            statement = select(Template).where(Template.id == template_id)
            result = await session.execute(statement)
            template = result.scalar_one_or_none()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            local_path = resolve_template_local_path(template)
            await session.delete(template)
            await session.commit()
        if local_path:
            try:
                os.remove(local_path)
            except FileNotFoundError:
                pass
            except OSError as exc:
                logger.warning(f"Could not remove template file {local_path}: {exc}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления макета")


@app.post("/templates/{template_id}/upload-to-telegram")
async def upload_template_to_telegram(
    template_id: int,
    tg_user_id: Optional[str] = Cookie(None)
):
    """Upload a template file to Telegram and update the template record with the file_id."""
    # Auth check
    if not tg_user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    try:
        requester_tg_id = int(tg_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    if not await check_admin_access(requester_tg_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Get template from database
    async with get_session() as session:
        statement = select(Template).where(Template.id == template_id)
        result = await session.execute(statement)
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check if template already has a Telegram file_id
        if template.file_id:
            return template
            
        # Check if template has a local file path
        if not template.path:
            raise HTTPException(status_code=400, detail="Template has no local file")
            
        # Construct full file path
        file_path = os.path.join(settings.base_dir, template.path)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Template file not found")
            
        # Return template with instruction to upload to Telegram
        # In a real implementation, this would trigger a background task
        # to upload the file to Telegram and update the template record
        return {
            "template": template,
            "file_path": file_path,
            "status": "ready_for_telegram_upload"
        }


@app.post("/templates")
async def create_template(payload: dict, tg_user_id: Optional[str] = Cookie(None)):
    """Create a new template. Only admins can create templates."""
    # Auth check
    if not tg_user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    try:
        requester_tg_id = int(tg_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Неверная авторизация")
    if not await check_admin_access(requester_tg_id):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Create template
    async with get_session() as session:
        template = Template(
            name=payload.get("name", ""),
            description=payload.get("description"),
            file_id=payload.get("file_id", ""),
            path=payload.get("path", ""),
            created_by=requester_tg_id
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Display a simple HTML dashboard with database content."""
    try:
        # Get counts for each table
        async with get_session() as session:
            users_count = await session.execute(select(User))
            users_count = len(users_count.scalars().all())
            
            admins_count = await session.execute(select(Admin))
            admins_count = len(admins_count.scalars().all())
            
            requests_count = await session.execute(select(Request))
            requests_count = len(requests_count.scalars().all())
            
            files_count = await session.execute(select(File))
            files_count = len(files_count.scalars().all())
            
            audit_count = await session.execute(select(Audit))
            audit_count = len(audit_count.scalars().all())

            templates_count = await session.execute(select(Template))
            templates_count = len(templates_count.scalars().all())
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Yandex GO Car Registration Bot - Dashboard</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                .stat-card {{
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 20px;
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #007bff;
                }}
                .stat-label {{
                    font-size: 1em;
                    color: #6c757d;
                }}
                .links {{
                    margin: 30px 0;
                    text-align: center;
                }}
                .links div {{
                    margin: 15px 0;
                }}
                .links h3 {{
                    margin: 5px 0;
                    color: #333;
                }}
                .format-links {{
                    text-align: center;
                }}
                .format-links a {{
                    margin: 0 5px;
                    padding: 5px 10px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                .format-links a:hover {{
                    background-color: #0056b3;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Yandex GO Car Registration Bot - Dashboard</h1>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{users_count}</div>
                        <div class="stat-label">Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{admins_count}</div>
                        <div class="stat-label">Admins</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{requests_count}</div>
                        <div class="stat-label">Requests</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{files_count}</div>
                        <div class="stat-label">Files</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{audit_count}</div>
                        <div class="stat-label">Audit Logs</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{templates_count}</div>
                        <div class="stat-label">Устаревшие макеты</div>
                    </div>
                </div>
                
                <div class="links">
                    <div>
                        <h3>Users</h3>
                        <div class="format-links">
                            <a href="/users/json">JSON</a> | 
                            <a href="/users/html">HTML</a>
                        </div>
                    </div>
                    <div>
                        <h3>Admins</h3>
                        <div class="format-links">
                            <a href="/admins/json">JSON</a> | 
                            <a href="/admins/html">HTML</a>
                        </div>
                    </div>
                    <div>
                        <h3>Requests</h3>
                        <div class="format-links">
                            <a href="/requests/json">JSON</a> | 
                            <a href="/requests/html">HTML</a>
                        </div>
                    </div>
                    <div>
                        <h3>Files</h3>
                        <div class="format-links">
                            <a href="/files/json">JSON</a> | 
                            <a href="/files/html">HTML</a>
                        </div>
                    </div>
                    <div>
                        <h3>Audit Logs</h3>
                        <div class="format-links">
                            <a href="/audit/json">JSON</a> | 
                            <a href="/audit/html">HTML</a>
                        </div>
                    </div>
                    <div>
                        <h3>Устаревшие макеты</h3>
                        <div class="format-links">
                            <a href="/templates/json">JSON</a> | 
                            <a href="/templates/html">HTML</a>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #6c757d;">
                    <p>Database Type: {settings.database_type}</p>
                    <p>Database URL: {settings.database_url}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        return HTMLResponse(content=f"<h1>Error generating dashboard: {e}</h1>", status_code=500)
