"""
Utility Functions

Common helper functions used across the application.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
from loguru import logger

from .config import get_settings, SUPPORTED_VIDEO_FORMATS


def generate_video_id() -> str:
    """Generate a unique video ID."""
    return str(uuid.uuid4())


def validate_file_extension(filename: str) -> bool:
    """Check if file has a supported video extension."""
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_VIDEO_FORMATS


def get_safe_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    sanitized = "".join(c if c in safe_chars else "_" for c in filename)
    
    # Ensure it has an extension
    if "." not in sanitized:
        sanitized += ".mp4"
    
    return sanitized


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as HH:MM:SS.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def cleanup_old_files(directory: Path, max_age_hours: int = 24) -> int:
    """
    Remove files older than max_age_hours.
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum age in hours
        
    Returns:
        Number of files removed
    """
    if not directory.exists():
        return 0
    
    removed = 0
    cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
    
    for file in directory.iterdir():
        if file.is_file() and file.stat().st_mtime < cutoff:
            try:
                file.unlink()
                removed += 1
            except Exception as e:
                logger.warning(f"Failed to remove {file}: {e}")
    
    return removed


def get_file_size_mb(path: str) -> float:
    """Get file size in megabytes."""
    return Path(path).stat().st_size / (1024 * 1024)
