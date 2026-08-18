"""
synthesize.py - Production Text-To-Speech (TTS) Provider Service
Supports evaluation of canopylabs/orpheus-v1-english with female voices:
- autumn (warm, natural, soft, companion-like default)
- diana
- hannah
Provides structured fallback signals to local WebSpeech adapter.
"""

import time
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from backend.app.config import (
    GROQ_API_KEY,
    GROQ_TTS_MODEL,
    GROQ_TTS_VOICE,
)
from backend.app.groq_client import get_async_groq_client

logger = logging.getLogger("meli.voice.tts")

router = APIRouter(prefix="/api/companion", tags=["voice"])

SUPPORTED_FEMALE_VOICES = {
    "autumn": {"description": "Warm, natural, soft, companion-like (Default)", "gender": "female"},
    "diana": {"description": "Crisp, calm, articulate", "gender": "female"},
    "hannah": {"description": "Gentle, expressive, friendly", "gender": "female"},
}


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize to speech")
    model: str = Field(default=GROQ_TTS_MODEL, description="TTS model identifier")
    voice: str = Field(default=GROQ_TTS_VOICE, description="Voice preset: autumn, diana, or hannah")


class TTSInfoResponse(BaseModel):
    provider: str
    model: str
    default_voice: str
    supported_voices: Dict[str, Any]
    fallback: str


@router.get("/tts/info", response_model=TTSInfoResponse)
async def get_tts_info() -> TTSInfoResponse:
    """Return available TTS model configuration and supported voices."""
    return TTSInfoResponse(
        provider="groq_orpheus_evaluator",
        model=GROQ_TTS_MODEL,
        default_voice=GROQ_TTS_VOICE,
        supported_voices=SUPPORTED_FEMALE_VOICES,
        fallback="web_speech",
    )


@router.post("/synthesize")
async def synthesize_speech(req: TTSRequest):
    """
    Synthesize text to speech using Orpheus model (canopylabs/orpheus-v1-english).
    If remote synthesis is not supported on the runtime Groq tier, returns a clean 200 JSON
    with fallback='web_speech' so the client plays via local WebSpeech synthesis.
    """
    t0 = time.perf_counter()
    clean_text = req.text.strip()
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text for speech synthesis cannot be empty.",
        )

    voice = req.voice if req.voice in SUPPORTED_FEMALE_VOICES else GROQ_TTS_VOICE
    model = req.model or GROQ_TTS_MODEL

    groq_client = get_async_groq_client()
    if not groq_client or not GROQ_API_KEY:
        return {
            "status": "fallback",
            "fallback": "web_speech",
            "reason": "missing_api_key",
            "voice": voice,
            "model": model,
        }

    try:
        # Check if Groq client exposes speech audio synthesis
        if hasattr(groq_client.audio, "speech") and hasattr(groq_client.audio.speech, "create"):
            audio_resp = await groq_client.audio.speech.create(
                model=model,
                voice=voice,
                input=clean_text,
                response_format="mp3",
            )
            audio_bytes = audio_resp.read() if hasattr(audio_resp, "read") else bytes(audio_resp)
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            logger.info(f"Synthesized {len(clean_text)} chars in {elapsed_ms}ms with {model} ({voice})")
            return Response(content=audio_bytes, media_type="audio/mpeg")
        else:
            # Remote speech synthesis endpoint is in evaluation; signal client to use tuned WebSpeech
            return {
                "status": "fallback",
                "fallback": "web_speech",
                "reason": "provider_in_evaluation",
                "voice": voice,
                "model": model,
                "message": "Using local tuned WebSpeech companion voice.",
            }
    except Exception as e:
        logger.warning(f"TTS synthesis exception (falling back to WebSpeech): {e}")
        return {
            "status": "fallback",
            "fallback": "web_speech",
            "reason": str(e),
            "voice": voice,
            "model": model,
        }
