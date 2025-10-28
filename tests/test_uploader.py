"""Tests for uploader service."""

import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.uploader import save_file


@pytest.mark.asyncio
async def test_save_file_fake_mode():
    """Test save_file in fake mode."""
    with patch('app.services.uploader.settings') as mock_settings:
        mock_settings.fake_files = True
        mock_settings.base_dir = "/tmp"
        mock_settings.upload_dir = "uploads"
        
        # Create a mock message
        mock_message = Mock()
        mock_message.photo = [Mock(file_id="test_file_id")]
        mock_message.bot = AsyncMock()
        
        # Call the function
        result = await save_file(mock_message, 123456789, "test.jpg")
        
        # In fake mode, it should return None
        assert result is None


@pytest.mark.asyncio
async def test_save_file_real_mode():
    """Test save_file in real mode."""
    with patch('app.services.uploader.settings') as mock_settings:
        mock_settings.fake_files = False
        mock_settings.base_dir = tempfile.gettempdir()
        mock_settings.upload_dir = "uploads"
        
        # Create a mock message
        mock_message = Mock()
        mock_message.photo = [Mock(file_id="test_file_id")]
        mock_message.bot = AsyncMock()
        mock_message.bot.get_file = AsyncMock(return_value=Mock(file_path="test_path"))
        mock_message.bot.download_file = AsyncMock()
        
        # Call the function
        result = await save_file(mock_message, 123456789, "test.jpg")
        
        # Check that the file path is returned
        expected_path = os.path.join(
            tempfile.gettempdir(), 
            "uploads", 
            "123456789", 
            "test.jpg"
        )
        assert result == expected_path
        
        # Check that the bot methods were called
        mock_message.bot.get_file.assert_called_once_with("test_file_id")
        mock_message.bot.download_file.assert_called_once_with("test_path", expected_path)