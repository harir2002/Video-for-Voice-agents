#!/usr/bin/env python3
"""
Generate audio files from conversation JSON using Sarvam AI or gTTS

Usage:
    python generate_audio.py ../../../conversations/generic-demo.json
    python generate_audio.py ../../../conversations/godrej-finance-demo.json
"""

import json
import sys
from pathlib import Path
import os

def generate_audio_from_json(json_path: str, use_sarvam: bool = True):
    """
    Generate audio files from conversation JSON
    
    Args:
        json_path: Path to conversation JSON file
        use_sarvam: Use Sarvam AI (True) or gTTS (False)
    """
    
    # Read JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        conversation = json.load(f)
    
    json_dir = Path(json_path).parent
    
    print(f"\n🎙️  Generating audio for: {conversation['title']}")
    print(f"📁 Location: {json_dir}\n")
    
    segments = conversation.get('segments', [])
    
    for i, segment in enumerate(segments):
        audio_file = segment.get('audioFile', '')
        transcript = segment.get('transcript', '')
        speaker = segment.get('speaker', 'unknown')
        
        if not audio_file or not transcript:
            print(f"⚠️  Segment {i+1}: Missing audioFile or transcript, skipping...")
            continue
        
        # Create full path
        full_path = json_dir / audio_file
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"📍 Segment {i+1} ({speaker}): {transcript[:50]}...")
        print(f"   → {full_path}")
        
        try:
            if use_sarvam:
                _generate_with_sarvam(full_path, transcript, speaker)
            else:
                _generate_with_gtts(full_path, transcript)
            print(f"   ✅ Generated\n")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}\n")

def _generate_with_sarvam(output_path: Path, text: str, speaker: str):
    """Generate audio using Sarvam AI TTS"""
    try:
        import sarvam
        
        api_key = os.getenv('SARVAM_API_KEY')
        if not api_key:
            raise Exception("SARVAM_API_KEY not set")
        
        client = sarvam.Client(api_key=api_key)
        
        # Detect language from text
        language = 'hi' if any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text) else 'en'
        
        response = client.text_to_speech(
            text=text,
            language=language,
            speaker=speaker
        )
        
        # Save audio
        with open(output_path, 'wb') as f:
            f.write(response)
            
    except ImportError:
        raise Exception("Sarvam not installed. Use: pip install sarvam")

def _generate_with_gtts(output_path: Path, text: str):
    """Generate audio using Google Text-to-Speech"""
    try:
        from gtts import gTTS
        
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(str(output_path))
        
    except ImportError:
        raise Exception("gTTS not installed. Use: pip install gtts")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_audio.py <path-to-conversation.json>")
        print("\nExamples:")
        print("  python generate_audio.py ../conversations/generic-demo.json")
        print("  python generate_audio.py ../conversations/godrej-finance-demo.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if not Path(json_path).exists():
        print(f"❌ File not found: {json_path}")
        sys.exit(1)
    
    # Try Sarvam first, fall back to gTTS
    try:
        generate_audio_from_json(json_path, use_sarvam=True)
    except Exception as e:
        print(f"⚠️  Sarvam failed: {e}")
        print("Trying gTTS instead...\n")
        try:
            generate_audio_from_json(json_path, use_sarvam=False)
        except Exception as e2:
            print(f"❌ gTTS also failed: {e2}")
            sys.exit(1)
