"""Pydantic schemas for data validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class UserCreate(BaseModel):
    """Schema for creating a user."""
    tg_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    tg_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime
    last_seen: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class RequestCreate(BaseModel):
    """Schema for creating a request."""
    user_id: int
    category: str
    has_brand: Optional[bool] = None
    year: Optional[int] = None
    has_license: Optional[bool] = None


class RequestResponse(BaseModel):
    """Schema for request response."""
    id: int
    user_id: int
    category: str
    status: str
    has_brand: Optional[bool] = None
    year: Optional[int] = None
    has_license: Optional[bool] = None
    created_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class FileCreate(BaseModel):
    """Schema for creating a file."""
    request_id: int
    kind: str
    file_id: str
    path: str


class FileResponse(BaseModel):
    """Schema for file response."""
    id: int
    request_id: int
    kind: str
    file_id: str
    path: str
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True