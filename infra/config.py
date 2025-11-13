"""Configuration management using pydantic-settings."""

import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )
    
    # Bot settings
    bot_token: str
    bot_username: str = "ndstrbot"
    admin_ids: List[int] = []
    
    # Web app settings
    web_app_base_url: str = "http://localhost:8000"
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./storage/app.db"
    database_type: str = "sqlite"  # sqlite or postgresql
    
    # Storage settings
    base_dir: str = os.getenv("BASE_DIR", "/app")  # Default to /app for Docker, can be overridden
    upload_dir: str = "storage/uploads"
    
    # Fake files mode
    fake_files: bool = False
    
    # Debug mode
    debug: bool = False
    
    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v, info):
        """Parse admin IDs from comma-separated string, JSON list, or single value."""
        if isinstance(v, int):
            return [v]
        elif isinstance(v, str):
            # Try JSON-like list without brackets
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return [int(x) for x in json.loads(v)]
                except Exception:
                    pass
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        elif isinstance(v, list):
            return [int(x) for x in v]
        return []
    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids_dup(cls, v, info):
        """(dup) Parse admin IDs—kept for compatibility."""
        return Settings.parse_admin_ids(v, info)

# Global settings instance
settings = Settings()
