"""
Transcription Service Layer

Abstracts transcription providers.
Automatically chunks large audio files for processing.
"""

import logging
import os
from typing import Optional, List
from pathlib import Path

from app.config import settings
from app.models import SegmentModel, TranscriptionResponse

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Main transcription service with provider abstraction"""
    
    # Audio chunk size: 30 seconds (safe for most APIs)
    CHUNK_DURATION_SECONDS = 30
    
    @staticmethod
    async def transcribe(
        file_path: str,
        language: str = "hi",
        service: Optional[str] = None
    ) -> TranscriptionResponse:
        """
        Transcribe audio file
        Automatically chunks large files for processing
        
        Args:
            file_path: Path to audio file
            language: Language code (hi, en, etc.)
            service: Override service
        
        Returns:
            TranscriptionResponse with transcript and segments
        """
        
        service = service or settings.TRANSCRIPTION_SERVICE
        
        try:
            file_name = Path(file_path).name
            logger.info(f"🎤 Transcribing: {file_name}")
            logger.info(f"   Language: {language}")
            logger.info(f"   Service: {service}")
            
            # Check if audio needs chunking
            needs_chunking = await TranscriptionService._check_needs_chunking(file_path)
            
            if needs_chunking:
                logger.info("📊 Large audio detected - automatic chunking enabled")
                return await TranscriptionService._transcribe_chunked(file_path, language, service)
            else:
                # Process directly
                return await TranscriptionService._transcribe_single(file_path, language, service)
        
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return TranscriptionResponse(
                success=False,
                transcript="",
                segments=[],
                duration=0,
                language="unknown",
                provider="error",
                error=str(e)
            )
    
    @staticmethod
    async def _check_needs_chunking(file_path: str) -> bool:
        """Check if audio file needs chunking based on file size"""
        
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Estimate duration: assume ~1MB = 1 minute of audio (varies by bitrate)
            estimated_minutes = file_size_mb / 1
            
            logger.info(f"📊 File size: {file_size_mb:.2f} MB (estimated {estimated_minutes:.1f} minutes)")
            
            # If > 1 minute, chunk it
            needs_chunking = estimated_minutes > 1
            
            if needs_chunking:
                logger.info("✅ Auto-chunking enabled for large file")
            
            return needs_chunking
        
        except Exception as e:
            logger.warning(f"Could not determine file size: {e}")
            return False
    
    @staticmethod
    async def _transcribe_chunked(
        file_path: str,
        language: str,
        service: str
    ) -> TranscriptionResponse:
        """Chunk audio file and transcribe each chunk"""
        
        try:
            from pydub import AudioSegment
            from pydub.utils import make_chunks
            import tempfile
            
            logger.info("🔄 Loading audio for chunking...")
            
            # Load audio
            audio = AudioSegment.from_file(file_path)
            duration_seconds = len(audio) / 1000
            
            logger.info(f"⏱️  Total duration: {duration_seconds:.1f} seconds")
            
            # Create chunks
            chunk_duration_ms = TranscriptionService.CHUNK_DURATION_SECONDS * 1000
            chunks = make_chunks(audio, chunk_duration_ms)
            
            logger.info(f"📦 Split into {len(chunks)} chunk(s)")
            
            # Transcribe each chunk
            all_transcripts = []
            all_segments = []
            current_time_offset = 0.0
            
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"\n📝 Processing chunk {i}/{len(chunks)}...")
                
                # Save chunk temporarily
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    chunk.export(tmp.name, format="wav")
                    tmp_path = tmp.name
                
                try:
                    # Transcribe chunk
                    result = await TranscriptionService._transcribe_single(tmp_path, language, service)
                    
                    if result.success:
                        chunk_text = result.transcript
                        logger.info(f"   ✅ Chunk {i}: {len(chunk_text)} chars")
                        all_transcripts.append(chunk_text)
                        
                        # Adjust segment times
                        for segment in result.segments:
                            adjusted_segment = SegmentModel(
                                text=segment.text,
                                start=segment.start + current_time_offset,
                                end=segment.end + current_time_offset,
                                confidence=segment.confidence
                            )
                            all_segments.append(adjusted_segment)
                    else:
                        logger.warning(f"   ⚠️  Chunk {i} failed: {result.error}")
                
                finally:
                    os.unlink(tmp_path)
                
                # Update time offset for next chunk
                current_time_offset += TranscriptionService.CHUNK_DURATION_SECONDS
            
            # Combine all transcripts
            combined_transcript = " ".join(all_transcripts)
            
            logger.info(f"\n✅ Chunked transcription complete!")
            logger.info(f"   Total transcript: {len(combined_transcript)} chars")
            logger.info(f"   Total segments: {len(all_segments)}")
            
            return TranscriptionResponse(
                success=True,
                transcript=combined_transcript,
                segments=all_segments,
                duration=duration_seconds,
                language=language,
                detected_languages=[language],
                provider=f"chunked-{service}",
                confidence=None,
                has_code_mixing=True
            )
        
        except ImportError:
            logger.error("pydub not installed - cannot chunk audio")
            logger.info("Attempting direct transcription without chunking...")
            return await TranscriptionService._transcribe_single(file_path, language, service)
        
        except Exception as e:
            logger.error(f"Chunking error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return TranscriptionResponse(
                success=False,
                transcript="",
                segments=[],
                duration=0,
                language="unknown",
                provider="error",
                error=f"Chunking failed: {str(e)}"
            )
    
    @staticmethod
    async def _transcribe_single(
        file_path: str,
        language: str,
        service: str
    ) -> TranscriptionResponse:
        """Transcribe a single audio file (or chunk)"""
        
        # Try the configured service
        if service == "mock":
            logger.info("🎭 Using mock transcript (for testing/fallback)")
            return TranscriptionService._get_mock_transcript(file_path, language)
        
        if service == "openrouter":
            result = await TranscriptionService._transcribe_openrouter(file_path, language)
            if result:
                return result
        
        if service == "sarvam":
            result = await TranscriptionService._transcribe_sarvam(file_path, language)
            if result:
                return result
        elif service == "groq":
            result = await TranscriptionService._transcribe_groq(file_path, language)
            if result:
                return result
        elif service == "google":
            result = await TranscriptionService._transcribe_google(file_path, language)
            if result:
                return result
        elif service == "assemblyai":
            result = await TranscriptionService._transcribe_assemblyai(file_path, language)
            if result:
                return result
        elif service == "openai":
            result = await TranscriptionService._transcribe_openai(file_path, language)
            if result:
                return result
        
        # Fallback: Try Groq if primary failed
        if service != "groq":
            logger.info("⚠️  Primary service failed, trying Groq as fallback...")
            result = await TranscriptionService._transcribe_groq(file_path, language)
            if result:
                return result
        
        # Final fallback: Return mock transcript
        logger.warning("⚠️  No transcription service available, using mock transcript")
        return TranscriptionService._get_mock_transcript(file_path, language)
    
    @staticmethod
    async def _transcribe_openrouter(file_path: str, language: str) -> Optional[TranscriptionResponse]:
        """Transcribe using OpenRouter API with Whisper model (reliable, multilingual)"""
        
        if not settings.OPENROUTER_API_KEY:
            logger.warning("⚠️  OpenRouter API key not configured")
            return None
        
        try:
            import httpx
            
            logger.info("📤 Using OpenRouter API (Whisper) for transcription")
            logger.info(f"   Model: {settings.OPENROUTER_STT_MODEL}")
            logger.info(f"   Language: {language}")
            
            # Read audio file
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            file_size_mb = len(audio_data) / (1024 * 1024)
            logger.info(f"   File size: {file_size_mb:.2f} MB")
            
            # OpenRouter API headers
            headers = {
                'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
                'HTTP-Referer': 'https://localhost:3000',
                'X-Title': settings.OPENROUTER_APP_NAME
            }
            
            # Prepare multipart form data for Whisper
            files = {
                'file': (Path(file_path).name, audio_data, 'audio/mpeg'),
                'model': (None, settings.OPENROUTER_STT_MODEL),
            }
            
            # Optional: set language if specified
            if language and language != 'unknown':
                files['language'] = (None, language)
            
            # Send to OpenRouter API
            logger.info("🔄 Sending audio to OpenRouter API...")
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    settings.OPENROUTER_STT_URL,
                    headers=headers,
                    files=files
                )
            
            logger.info(f"   Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ OpenRouter API error: {response.status_code}")
                logger.error(response.text)
                return None
            
            result_data = response.json()
            transcript = result_data.get('text', '')
            
            logger.info(f"✅ OpenRouter transcription complete: {len(transcript)} chars")
            
            segments = TranscriptionService._create_segments(transcript)
            
            return TranscriptionResponse(
                success=True,
                transcript=transcript,
                segments=segments,
                duration=0,
                language=language,
                detected_languages=[language],
                provider="openrouter",
                confidence=None,
                has_code_mixing=False
            )
        
        except Exception as e:
            logger.error(f"❌ OpenRouter error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    async def _transcribe_google(file_path: str, language: str) -> Optional[TranscriptionResponse]:
        """Transcribe using Google Cloud Speech-to-Text"""
        
        if not settings.GOOGLE_CLOUD_PROJECT_ID:
            logger.warning("Google Cloud not configured")
            return None
        
        try:
            logger.info("📤 Using Google Cloud Speech-to-Text")
            
            # TODO: Implement Google Cloud integration
            # from google.cloud import speech_v1
            # client = speech_v1.SpeechClient()
            
            logger.warning("⚠️  Google Cloud integration not yet implemented")
            return None
        
        except Exception as e:
            logger.error(f"Google Cloud error: {str(e)}")
            return None
    
    @staticmethod
    async def _transcribe_groq(file_path: str, language: str) -> Optional[TranscriptionResponse]:
        """Transcribe using Groq API with Whisper model (fast, multilingual)"""
        
        if not settings.GROQ_API_KEY:
            logger.warning("⚠️  Groq API key not configured")
            return None
        
        try:
            import httpx
            
            logger.info("📤 Using Groq API (Whisper) for transcription")
            logger.info(f"   Model: {settings.GROQ_STT_MODEL}")
            logger.info(f"   Language: {language}")
            
            # Read audio file
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            file_size_mb = len(audio_data) / (1024 * 1024)
            logger.info(f"   File size: {file_size_mb:.2f} MB")
            
            # Groq API endpoint and headers
            headers = {
                'Authorization': f'Bearer {settings.GROQ_API_KEY}'
            }
            
            # Prepare multipart form data
            files = {
                'file': (Path(file_path).name, audio_data, 'audio/mpeg'),
                'model': (None, settings.GROQ_STT_MODEL),
                'language': (None, language)
            }
            
            # Send to Groq API
            logger.info("🔄 Sending audio to Groq API...")
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    'https://api.groq.com/openai/v1/audio/transcriptions',
                    headers=headers,
                    files=files
                )
            
            logger.info(f"   Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ Groq API error: {response.status_code}")
                logger.error(response.text)
                return None
            
            result_data = response.json()
            transcript = result_data.get('text', '')
            
            logger.info(f"✅ Groq transcription complete: {len(transcript)} chars")
            
            segments = TranscriptionService._create_segments(transcript)
            
            return TranscriptionResponse(
                success=True,
                transcript=transcript,
                segments=segments,
                duration=0,
                language=language,
                detected_languages=[language],
                provider="groq",
                confidence=None,
                has_code_mixing=False
            )
        
        except Exception as e:
            logger.error(f"❌ Groq error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    async def _transcribe_sarvam(file_path: str, language: str) -> Optional[TranscriptionResponse]:
        """Transcribe using Sarvam AI (supports Hindi, Hinglish, 12+ Indian languages)"""
        
        if not settings.SARVAM_API_KEY:
            logger.warning("⚠️  Sarvam API key not configured - fallback to mock")
            return None
        
        try:
            import httpx
            
            logger.info("📤 Using Sarvam AI for transcription")
            logger.info(f"   Model: {settings.SARVAM_STT_MODEL}")
            logger.info(f"   Language: {language}")
            
            # Read audio file
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            file_size_mb = len(audio_data) / (1024 * 1024)
            logger.info(f"   File size: {file_size_mb:.2f} MB")
            
            # Prepare request
            headers = {
                'Authorization': f'Bearer {settings.SARVAM_API_KEY}',
                'Content-Type': 'application/octet-stream'
            }
            
            payload = {
                'model': settings.SARVAM_STT_MODEL,
                'language_code': settings.SARVAM_STT_LANGUAGE,
                'mode': settings.SARVAM_STT_MODE
            }
            
            # Send to Sarvam API
            logger.info("🔄 Sending audio to Sarvam API...")
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    settings.SARVAM_STT_URL,
                    headers=headers,
                    params=payload,
                    content=audio_data
                )
            
            logger.info(f"   Response status: {response.status_code}")
            
            if response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', '')
                logger.warning(f"⚠️  Sarvam API error (400): {error_msg}")
                
                # If it's a duration error, we should have caught it in chunking
                if "exceeds" in error_msg.lower() or "duration" in error_msg.lower():
                    logger.warning("   Audio exceeds duration limit - consider chunking")
                    return None
            
            if response.status_code != 200:
                logger.error(f"❌ Sarvam API error: {response.status_code}")
                logger.error(response.text)
                return None
            
            result_data = response.json()
            
            if not result_data.get('success'):
                logger.error(f"❌ Sarvam transcription failed: {result_data}")
                return None
            
            transcript = result_data.get('transcript', '')
            logger.info(f"✅ Sarvam transcription complete: {len(transcript)} chars")
            
            segments = TranscriptionService._create_segments(transcript)
            
            return TranscriptionResponse(
                success=True,
                transcript=transcript,
                segments=segments,
                duration=0,
                language=language,
                detected_languages=[language],
                provider="sarvam",
                confidence=None,
                has_code_mixing=True
            )
        
        except Exception as e:
            logger.error(f"❌ Sarvam error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    async def _transcribe_assemblyai(file_path: str, language: str) -> Optional[TranscriptionResponse]:
        """Transcribe using AssemblyAI (supports long audio)"""
        
        if not settings.ASSEMBLYAI_API_KEY:
            logger.warning("AssemblyAI not configured")
            return None
        
        try:
            logger.info("📤 Using AssemblyAI for transcription")
            
            import httpx
            
            # Read audio file
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            file_size_mb = len(audio_data) / (1024 * 1024)
            logger.info(f"   File size: {file_size_mb:.2f} MB")
            
            headers = {
                'Authorization': settings.ASSEMBLYAI_API_KEY,
                'Content-Type': 'application/octet-stream'
            }
            
            # Upload audio to AssemblyAI
            logger.info("📤 Uploading to AssemblyAI...")
            async with httpx.AsyncClient() as client:
                upload_response = await client.post(
                    'https://api.assemblyai.com/v2/upload',
                    headers=headers,
                    content=audio_data,
                    timeout=180.0
                )
            
            if upload_response.status_code != 200:
                logger.error(f"Upload failed: {upload_response.status_code}")
                logger.error(upload_response.text)
                return None
            
            audio_url = upload_response.json().get('upload_url')
            logger.info(f"✅ Audio uploaded: {audio_url}")
            
            # Submit transcription
            logger.info("📋 Submitting transcription request...")
            transcript_data = {
                'audio_url': audio_url,
                'language_code': language
            }
            
            async with httpx.AsyncClient() as client:
                submit_response = await client.post(
                    'https://api.assemblyai.com/v2/transcript',
                    headers=headers,
                    json=transcript_data,
                    timeout=30.0
                )
            
            if submit_response.status_code != 200:
                logger.error(f"Submission failed: {submit_response.status_code}")
                return None
            
            transcript_id = submit_response.json().get('id')
            logger.info(f"✅ Transcription submitted: {transcript_id}")
            logger.info("⏳ Processing audio...")
            
            # Poll for results
            import asyncio
            max_attempts = 120  # 2 minutes
            attempt = 0
            
            async with httpx.AsyncClient() as client:
                while attempt < max_attempts:
                    poll_response = await client.get(
                        f'https://api.assemblyai.com/v2/transcript/{transcript_id}',
                        headers=headers,
                        timeout=30.0
                    )
                    
                    result = poll_response.json()
                    status = result.get('status')
                    
                    if status == 'completed':
                        text = result.get('text', '')
                        logger.info(f"✅ Transcription complete: {len(text)} chars")
                        
                        segments = TranscriptionService._create_segments(text)
                        
                        return TranscriptionResponse(
                            success=True,
                            transcript=text,
                            segments=segments,
                            duration=result.get('audio_duration_seconds', 0),
                            language=language,
                            detected_languages=[language],
                            provider="assemblyai",
                            confidence=None,
                            has_code_mixing=False
                        )
                    
                    elif status == 'error':
                        error = result.get('error')
                        logger.error(f"Transcription error: {error}")
                        return None
                    
                    # Still processing
                    attempt += 1
                    if attempt % 10 == 0:
                        logger.info(f"   Status: {status} ({attempt}s elapsed)")
                    
                    await asyncio.sleep(1)
            
            logger.error("Transcription timeout")
            return None
        
        except Exception as e:
            logger.error(f"AssemblyAI error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    async def _transcribe_openai(file_path: str, language: str) -> Optional[TranscriptionResponse]:
        """Transcribe using OpenAI Whisper"""
        
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI not configured")
            return None
        
        try:
            from openai import OpenAI
            import tempfile
            
            logger.info("📤 Using OpenAI Whisper")
            
            # Read audio file
            with open(file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            file_ext = Path(file_path).suffix.lstrip('.').lower()
            
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix=f'.{file_ext}', delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            try:
                with open(tmp_path, 'rb') as audio_file:
                    logger.info("🎤 Sending to OpenAI...")
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language
                    )
                
                text = transcript.text if hasattr(transcript, 'text') else str(transcript)
                logger.info(f"✅ OpenAI transcription complete: {len(text)} chars")
                
                segments = TranscriptionService._create_segments(text)
                
                return TranscriptionResponse(
                    success=True,
                    transcript=text,
                    segments=segments,
                    duration=0,
                    language=language,
                    detected_languages=[language],
                    provider="openai",
                    confidence=None,
                    has_code_mixing=False
                )
            
            finally:
                os.unlink(tmp_path)
        
        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            return None
    
    @staticmethod
    def _get_mock_transcript(file_path: str, language: str) -> TranscriptionResponse:
        """Return a mock transcript for testing"""
        
        logger.info("🎭 Using MOCK transcript (for testing)")
        
        # Simple mock transcript
        mock_text = f"""नमस्ते! यह एक demo transcription है। 
This is a Hinglish audio file that would normally be transcribed by our service.
आप इस audio को play कर सकते हैं और देख सकते हैं कि player कैसे काम करता है।
The actual transcription will appear here when the service is configured."""
        
        segments = TranscriptionService._create_segments(mock_text)
        
        return TranscriptionResponse(
            success=True,
            transcript=mock_text,
            segments=segments,
            duration=0,
            language=language,
            detected_languages=[language],
            provider="mock",
            confidence=None,
            has_code_mixing=True
        )
    
    @staticmethod
    def _create_segments(transcript: str, words_per_segment: int = 5) -> List[SegmentModel]:
        """Convert transcript into segments"""
        
        if not transcript:
            return []
        
        words = transcript.split()
        segments = []
        current_time = 0.0
        
        # Estimate: 150 words/min = 2.5 words/sec
        words_per_second = 2.5
        
        for i in range(0, len(words), words_per_segment):
            chunk_words = words[i:i + words_per_segment]
            chunk_text = " ".join(chunk_words)
            duration = len(chunk_words) / words_per_second
            
            segment = SegmentModel(
                text=chunk_text,
                start=current_time,
                end=current_time + duration,
                confidence=0.95
            )
            segments.append(segment)
            current_time += duration
        
        return segments


