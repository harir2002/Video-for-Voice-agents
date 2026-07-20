"""
Transcription Routes

Handles audio file upload and transcription requests
"""

import logging
import os
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from app.config import settings
from app.models import TranscriptionResponse, ErrorResponse
from app.services.transcription import TranscriptionService
from app.utils.validation import validate_audio_file

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(default="hi")
):
    """
    Upload and transcribe an audio file
    
    - **audio**: Audio file (MP3, WAV, M4A, OGG, WEBM)
    - **language**: Language code (hi for Hindi, en for English, etc.)
    
    Returns:
        TranscriptionResponse with transcript and segments
    """
    
    # Validate language code
    if not language or len(language) > 5:
        language = "hi"  # Default to Hindi for Hinglish
    
    temp_file_path = None
    
    try:
        # Save uploaded file temporarily
        temp_dir = Path(settings.UPLOAD_TEMP_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique filename
        temp_file_path = temp_dir / f"{audio.filename}"
        
        # Validate before saving
        file_content = await audio.read()
        
        # Check file size
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )
        
        # Check file extension
        file_ext = Path(audio.filename).suffix.lstrip(".").lower()
        if file_ext not in settings.ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
            )
        
        # Save file
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"📁 Saved upload: {temp_file_path}")
        
        # Transcribe
        logger.info(f"🎤 Transcribing: {audio.filename} (language: {language})")
        result = await TranscriptionService.transcribe(
            str(temp_file_path),
            language=language
        )
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=result.error or "Transcription failed"
            )
        
        logger.info(f"✅ Transcription successful: {len(result.transcript)} chars")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Transcription error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"🗑️  Cleaned up: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file_path}: {e}")

@router.get("/transcribe/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "success": True,
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "Hindi"},
            {"code": "hi-en", "name": "Hinglish (Hindi + English)"},
            {"code": "ta", "name": "Tamil"},
            {"code": "te", "name": "Telugu"},
            {"code": "mr", "name": "Marathi"},
            {"code": "kn", "name": "Kannada"},
            {"code": "ml", "name": "Malayalam"},
            {"code": "gu", "name": "Gujarati"},
            {"code": "bn", "name": "Bengali"},
            {"code": "pa", "name": "Punjabi"},
        ]
    }
