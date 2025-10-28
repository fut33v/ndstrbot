"""Configuration management using pydantic-settings."""

import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Bot settings
    bot_token: str
    admin_ids: List[int] = []
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./storage/app.db"
    
    # Storage settings
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir: str = "storage/uploads"
    
    # Fake files mode
    fake_files: bool = False
    
    # Debug mode
    debug: bool = False
    
    @field_validator("admin_ids", mode="before")
    def parse_admin_ids(cls, v):
        """Parse admin IDs from comma-separated string or single value."""
        if isinstance(v, int):
            return [v]
        elif isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        elif isinstance(v, list):
            return [int(x) for x in v]
        return []

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()