#!/usr/bin/env python3
"""
Debug configuration loading
Helps verify that .env file is being read correctly
"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("\n" + "="*60)
print("🔍 CONFIGURATION DEBUG")
print("="*60)

# Check if .env file exists
env_file = Path('.env')
print(f"\n📁 .env file location: {env_file.absolute()}")
print(f"   Exists: {'✅ Yes' if env_file.exists() else '❌ No'}")

# Load .env manually
print("\n📖 Loading .env file...")
load_dotenv(override=True)

# Check environment variables
print("\n🔑 Environment Variables:")
keys_to_check = [
    'OPENAI_API_KEY',
    'OPENAI_BASE_URL',
    'SARVAM_API_KEY',
    'TRANSCRIPTION_SERVICE',
    'PORT',
    'ENVIRONMENT'
]

for key in keys_to_check:
    value = os.getenv(key)
    if value:
        # Mask API keys for security
        if 'API_KEY' in key:
            masked = value[:10] + '...' + value[-10:] if len(value) > 20 else '***'
            print(f"   {key}: {masked} ✅")
        else:
            print(f"   {key}: {value} ✅")
    else:
        print(f"   {key}: <NOT SET> ❌")

# Load Pydantic settings
print("\n⚙️  Loading Pydantic Settings...")
try:
    from app.config import settings
    print("   ✅ Settings loaded successfully")
    
    print("\n📊 Settings Values:")
    print(f"   OPENAI_API_KEY: {'✅ Present' if settings.OPENAI_API_KEY else '❌ Empty'}")
    print(f"   OPENAI_BASE_URL: {settings.OPENAI_BASE_URL}")
    print(f"   TRANSCRIPTION_SERVICE: {settings.TRANSCRIPTION_SERVICE}")
    print(f"   PORT: {settings.PORT}")
    
except Exception as e:
    print(f"   ❌ Error loading settings: {e}")

print("\n" + "="*60)
print("✅ Debug complete!")
print("="*60 + "\n")
