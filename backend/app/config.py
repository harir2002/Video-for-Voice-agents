"""
Configuration Management

Loads and validates environment variables for the application.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path
import os
import json

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Server
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    ENVIRONMENT: str = Field(default="development")
    
    # CORS
    CORS_ORIGIN: str = Field(default="http://localhost:3000")
    
    # File Upload
    UPLOAD_TEMP_DIR: str = Field(default="./tmp")
    MAX_FILE_SIZE: int = Field(default=25 * 1024 * 1024)  # 25MB
    ALLOWED_AUDIO_TYPES: list = Field(default=["mp3", "wav", "m4a", "ogg", "webm"])
    
    # Transcription Services
    TRANSCRIPTION_SERVICE: str = Field(default="openrouter")  # openrouter, sarvam, groq, google, assemblyai, openai, mock
    
    # OpenRouter API (Whisper STT - Reliable)
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_STT_MODEL: str = Field(default="openai/whisper-1")
    OPENROUTER_STT_URL: str = Field(default="https://openrouter.ai/api/v1/audio/transcriptions")
    OPENROUTER_APP_NAME: str = Field(default="Voice Demo Studio")
    
    # Groq API (Whisper STT - Fast, multilingual)
    GROQ_API_KEY: str = Field(default="")
    GROQ_STT_MODEL: str = Field(default="whisper-large-v3")
    
    # Sarvam AI
    SARVAM_API_KEY: str = Field(default="")
    SARVAM_STT_URL: str = Field(default="https://api.sarvam.ai/speech-to-text")
    SARVAM_STT_MODEL: str = Field(default="saaras:v3")
    SARVAM_STT_MODE: str = Field(default="transcribe")
    SARVAM_STT_LANGUAGE: str = Field(default="unknown")
    
    # Google Cloud Speech-to-Text
    GOOGLE_CLOUD_PROJECT_ID: str = Field(default="")
    GOOGLE_CLOUD_CREDENTIALS_JSON: str = Field(default="{}")
    
    # AssemblyAI
    ASSEMBLYAI_API_KEY: str = Field(default="")
    
    # OpenAI (Fallback)
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1")
    
    # OpenRouter (For LLM chat)
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_LLM_MODEL: str = Field(default="google/gemma-4-26b-a4b-it")
    OPENROUTER_LLM_URL: str = Field(default="https://openrouter.ai/api/v1/chat/completions")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    @field_validator('ALLOWED_AUDIO_TYPES', mode='before')
    @classmethod
    def validate_audio_types(cls, v):
        """Convert comma-separated string to list"""
        if isinstance(v, str):
            return [t.strip() for t in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

# Manually load .env file to ensure variables are available
from dotenv import load_dotenv
load_dotenv(override=True)

# Create settings instance
settings = Settings()

# Debug: Print loaded configuration
import logging
logger = logging.getLogger(__name__)
logger.info(f"Transcription Service: {settings.TRANSCRIPTION_SERVICE}")

if settings.TRANSCRIPTION_SERVICE == "openrouter":
    logger.info(f"✅ OpenRouter API configured: {'Yes' if settings.OPENROUTER_API_KEY else 'No API key'}")
    logger.info(f"   Model: {settings.OPENROUTER_STT_MODEL}")
    logger.info(f"   URL: {settings.OPENROUTER_STT_URL}")
elif settings.TRANSCRIPTION_SERVICE == "mock":
    logger.info(f"🎭 MOCK transcription enabled (for testing/development)")
elif settings.TRANSCRIPTION_SERVICE == "groq":
    logger.info(f"✅ Groq API configured: {'Yes' if settings.GROQ_API_KEY else 'No API key'}")
    logger.info(f"   Model: {settings.GROQ_STT_MODEL}")
elif settings.TRANSCRIPTION_SERVICE == "sarvam":
    logger.info(f"✅ Sarvam AI configured: {'Yes' if settings.SARVAM_API_KEY else 'No API key'}")
    logger.info(f"   Model: {settings.SARVAM_STT_MODEL}")
    logger.info(f"   Language: {settings.SARVAM_STT_LANGUAGE}")
    logger.info(f"   URL: {settings.SARVAM_STT_URL}")
elif settings.TRANSCRIPTION_SERVICE == "google":
    logger.info(f"✅ Google Cloud Speech-to-Text configured")
    logger.info(f"   Project ID: {settings.GOOGLE_CLOUD_PROJECT_ID[:20] if settings.GOOGLE_CLOUD_PROJECT_ID else 'Not set'}")
elif settings.TRANSCRIPTION_SERVICE == "assemblyai":
    logger.info(f"✅ AssemblyAI configured: {'Yes' if settings.ASSEMBLYAI_API_KEY else 'No API key'}")
elif settings.TRANSCRIPTION_SERVICE == "openai":
    logger.info(f"✅ OpenAI Whisper configured: {'Yes' if settings.OPENAI_API_KEY else 'No API key'}")

