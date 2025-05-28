import os
import mimetypes
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def validate_pdf_file(filename: str, file_content: bytes) -> tuple[bool, Optional[str]]:
    """
    Validate if the uploaded file is a valid PDF
    
    Args:
        filename: Original filename
        file_content: File content as bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file extension
    if not filename.lower().endswith('.pdf'):
        return False, "File must have .pdf extension"
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type != 'application/pdf':
        logger.warning(f"MIME type mismatch for {filename}: {mime_type}")
    
    # Check PDF magic bytes
    if not file_content.startswith(b'%PDF-'):
        return False, "File does not appear to be a valid PDF"
    
    return True, None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing or replacing potentially dangerous characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and other potentially dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:250 - len(ext)] + ext
    
    return sanitized


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text for logging purposes
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..." 