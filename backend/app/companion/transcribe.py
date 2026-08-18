"""
transcribe.py - Production Audio Transcription Service powered by Groq Whisper
"""

import time
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from backend.app.config import (
    GROQ_API_KEY,
    GROQ_STT_MODEL,
    GROQ_STT_TURBO_MODEL,
    GROQ_STT_ACCURATE_MODEL,
)
from backend.app.groq_client import get_async_groq_client

logger = logging.getLogger("meli.voice.transcribe")

router = APIRouter(prefix="/api/companion", tags=["voice"])

MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25MB max
ALLOWED_MIME_PREFIXES = ("audio/", "video/webm", "application/octet-stream")
ALLOWED_EXTENSIONS = (".webm", ".wav", ".mp3", ".m4a", ".ogg", ".mp4", ".flac")


@router.post("/transcribe")
async def transcribe_audio(
    request: Request,
) -> Dict[str, Any]:
    """
    Transcribe uploaded user speech audio using Groq Whisper model.
    Accepts raw audio binary stream (with Content-Type and optional X-Audio-Filename header).
    Supports X-Accuracy-Mode: 'accurate' (whisper-large-v3) or 'turbo' (whisper-large-v3-turbo).
    Audio is processed ephemerally without permanent storage.
    """
    t0 = time.perf_counter()

    content_type = request.headers.get("content-type", "audio/webm").split(";")[0].strip().lower()
    filename = request.headers.get("x-audio-filename", "recording.webm").strip()
    accuracy_mode = request.headers.get("x-accuracy-mode", "turbo").strip().lower()
    stt_model = GROQ_STT_ACCURATE_MODEL if accuracy_mode == "accurate" else GROQ_STT_TURBO_MODEL
    filename_lower = filename.lower()

    # Validate audio MIME / extension
    is_valid_type = (
        any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES)
        or any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS)
    )
    if not is_valid_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio type '{content_type}'. Supported formats: webm, wav, mp3, m4a, ogg, mp4.",
        )

    # Read audio bytes ephemerally
    try:
        audio_bytes = await request.body()
    except Exception as e:
        logger.error(f"Failed to read audio upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded audio file.",
        )

    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is empty.",
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file size exceeds maximum limit of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    groq_client = get_async_groq_client()
    if not groq_client or not GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq transcription client is not configured (missing GROQ_API_KEY).",
        )

    # Transcribe via Groq Whisper API
    try:
        # Determine normalized filename for Groq client tuple
        safe_filename = filename if any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS) else f"{filename}.webm"

        transcription = await groq_client.audio.transcriptions.create(
            file=(safe_filename, audio_bytes),
            model=stt_model,
            response_format="json",
            temperature=0.0,
        )

        transcript_text = transcription.text.strip() if hasattr(transcription, "text") else str(transcription).strip()
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        logger.info(f"Transcription completed in {elapsed_ms}ms using {stt_model}: '{transcript_text[:50]}...'")

        return {
            "transcript": transcript_text,
            "model": stt_model,
            "duration_ms": elapsed_ms,
            "filename": filename,
        }

    except Exception as e:
        logger.error(f"Groq Whisper transcription exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Speech-to-text transcription service error: {str(e)}",
        )
