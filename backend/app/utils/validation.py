"""
File Validation Utilities
"""

from pathlib import Path
from app.config import settings

def validate_audio_file(file_path: str) -> dict:
    """
    Validate audio file
    
    Args:
        file_path: Path to audio file
    
    Returns:
        dict with valid (bool), errors (list), and file info
    """
    errors = []
    
    # Check file exists
    path = Path(file_path)
    if not path.exists():
        errors.append("File does not exist")
        return {"valid": False, "errors": errors}
    
    # Check file size
    file_size = path.stat().st_size
    if file_size > settings.MAX_FILE_SIZE:
        errors.append(
            f"File size ({file_size / (1024*1024):.1f}MB) exceeds "
            f"maximum ({settings.MAX_FILE_SIZE / (1024*1024):.0f}MB)"
        )
    
    # Check file extension
    ext = path.suffix.lstrip(".").lower()
    if ext not in settings.ALLOWED_AUDIO_TYPES:
        errors.append(
            f"File type .{ext} not allowed. "
            f"Allowed: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
        )
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "file_name": path.name,
        "file_size": file_size,
        "file_type": ext
    }
