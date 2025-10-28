"""Tests for validator functions."""

import pytest
from app.services.validators import validate_year, validate_photo_content_type


def test_validate_year_valid():
    """Test validate_year with valid years."""
    # Test current year
    is_valid, year = validate_year("2025")
    assert is_valid is True
    assert year == 2025
    
    # Test minimum year
    is_valid, year = validate_year("1980")
    assert is_valid is True
    assert year == 1980
    
    # Test middle year
    is_valid, year = validate_year("2000")
    assert is_valid is True
    assert year == 2000


def test_validate_year_invalid():
    """Test validate_year with invalid years."""
    # Test year too low
    is_valid, year = validate_year("1979")
    assert is_valid is False
    
    # Test year too high
    is_valid, year = validate_year("2026")
    assert is_valid is False
    
    # Test non-numeric input
    is_valid, year = validate_year("abc")
    assert is_valid is False
    
    # Test empty input
    is_valid, year = validate_year("")
    assert is_valid is False


def test_validate_photo_content_type():
    """Test validate_photo_content_type."""
    # Valid content types
    assert validate_photo_content_type("image/jpeg") is True
    assert validate_photo_content_type("image/png") is True
    
    # Invalid content types
    assert validate_photo_content_type("image/gif") is False
    assert validate_photo_content_type("text/plain") is False
    assert validate_photo_content_type("") is False