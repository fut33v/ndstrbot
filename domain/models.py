"""Database models using SQLModel."""

from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """User model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tg_id: int = Field(unique=True, index=True)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    requests: List["Request"] = Relationship(back_populates="user")


class Admin(SQLModel, table=True):
    """Admin model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tg_id: Optional[int] = Field(default=None, unique=True, index=True)
    username: Optional[str] = Field(default=None, unique=True, index=True)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: Optional[int] = Field(default=None)  # TG ID of admin who added this admin


class Request(SQLModel, table=True):
    """Request model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    category: str = Field()  # 'легковой' or 'грузовой'
    status: str = Field(default="draft")  # draft, submitted, approved, rejected
    has_brand: Optional[bool] = None
    year: Optional[int] = None
    has_license: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    
    # Relationships
    user: User = Relationship(back_populates="requests")
    files: List["File"] = Relationship(back_populates="request")


class File(SQLModel, table=True):
    """File model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="request.id", index=True)
    kind: str = Field()  # 'auto_photo' or 'sts_photo'
    file_id: str = Field()  # Telegram file ID
    path: str = Field()  # Local file path
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    request: Request = Relationship(back_populates="files")


class Audit(SQLModel, table=True):
    """Audit log model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    event: str = Field()
    payload: str = Field()  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)