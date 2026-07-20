"""
Voice Demo Studio - Python FastAPI Backend

A production-ready backend for handling audio transcription and conversation management.
Supports Hinglish (Hindi + English), OpenAI Whisper, and Sarvam AI transcription services.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import health, transcribe
from app.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Voice Demo Studio Backend",
    description="Audio transcription and conversation management API",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(transcribe.router, prefix="/api", tags=["Transcription"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Voice Demo Studio Backend Starting...")
    logger.info(f"📡 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🎤 Transcription Service: {settings.TRANSCRIPTION_SERVICE}")
    logger.info(f"📁 Temp directory: {settings.UPLOAD_TEMP_DIR}")
    
    # Ensure temp directory exists
    os.makedirs(settings.UPLOAD_TEMP_DIR, exist_ok=True)
    logger.info("✅ Backend initialized successfully")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voice Demo Studio API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"\n🎙️  Voice Demo Studio - Backend")
    logger.info(f"\n📡 Starting server on http://localhost:{settings.PORT}")
    logger.info(f"🔧 Environment: {settings.ENVIRONMENT}")
    logger.info(f"📁 Temp directory: {settings.UPLOAD_TEMP_DIR}\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )
