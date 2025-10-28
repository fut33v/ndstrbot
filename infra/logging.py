"""Logging configuration."""

import logging
import os
from logging.handlers import RotatingFileHandler

from infra.config import settings


def setup_logging():
    """Set up logging with rotation."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(settings.base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create rotating file handler for general logs
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, "app.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Create rotating file handler for error logs
    error_handler = RotatingFileHandler(
        os.path.join(logs_dir, "error.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Set specific log levels for our modules
    logging.getLogger('app').setLevel(logging.DEBUG if settings.debug else logging.INFO)
    logging.getLogger('infra').setLevel(logging.DEBUG if settings.debug else logging.INFO)