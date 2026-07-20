"""
Pydantic Models for Request/Response validation
"""

from pydantic import BaseModel
from typing import Optional, List

class SegmentModel(BaseModel):
    """Transcription segment with timing"""
    text: str
    start: float
    end: float
    confidence: float = 0.95
    languages: Optional[List[str]] = None

class TranscriptionResponse(BaseModel):
    """Transcription API response"""
    success: bool
    transcript: str
    segments: List[SegmentModel] = []
    duration: float
    language: str
    detected_languages: Optional[List[str]] = None
    provider: str
    confidence: Optional[float] = None
    has_code_mixing: bool = False
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    environment: str
    transcription_service: str
    has_openai_key: bool

class ErrorResponse(BaseModel):
    """Error response"""
    success: bool
    error: str
    details: Optional[str] = None
