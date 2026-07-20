"""
Health Check Endpoints
"""

from fastapi import APIRouter
from app.config import settings
from app.models import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns the status of the backend and available services
    """
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        transcription_service=settings.TRANSCRIPTION_SERVICE,
        has_openai_key=bool(settings.OPENAI_API_KEY)
    )

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voice Demo Studio API",
        "version": "1.0.0",
        "docs": "/docs"
    }
