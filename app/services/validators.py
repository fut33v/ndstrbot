"""Validation services."""

import datetime


def validate_year(year_str: str) -> tuple[bool, int]:
    """
    Validate car year.
    
    Args:
        year_str: Year as string
        
    Returns:
        Tuple of (is_valid, year_int)
    """
    try:
        year = int(year_str)
        current_year = datetime.datetime.now().year
        if 1980 <= year <= current_year:
            return True, year
        return False, year
    except ValueError:
        return False, 0


def validate_photo_content_type(content_type: str) -> bool:
    """
    Validate photo content type.
    
    Args:
        content_type: Content type of the file
        
    Returns:
        True if valid photo content type
    """
    valid_types = ["image/jpeg", "image/png"]
    return content_type in valid_types