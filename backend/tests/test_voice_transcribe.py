"""
test_voice_transcribe.py - Unit & Integration Tests for Voice Transcription Endpoint
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import GROQ_STT_MODEL

client = TestClient(app)


def test_01_transcribe_valid_audio():
    """Verify POST /api/companion/transcribe parses audio and returns transcription."""
    mock_transcription = MagicMock()
    mock_transcription.text = "Hello Meli, what can you help me with?"

    mock_groq_client = MagicMock()
    mock_groq_client.audio = MagicMock()
    mock_groq_client.audio.transcriptions = MagicMock()
    mock_groq_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)

    with patch("backend.app.companion.transcribe.get_async_groq_client", return_value=mock_groq_client), \
         patch("backend.app.companion.transcribe.GROQ_API_KEY", "mock_key"):
        fake_audio_bytes = b"fake_webm_audio_bytes_12345"
        response = client.post(
            "/api/companion/transcribe",
            content=fake_audio_bytes,
            headers={
                "Content-Type": "audio/webm",
                "X-Audio-Filename": "recording.webm",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == "Hello Meli, what can you help me with?"
        assert data["model"] == GROQ_STT_MODEL
        assert "duration_ms" in data
        assert data["filename"] == "recording.webm"


def test_02_transcribe_empty_file():
    """Verify POST /api/companion/transcribe rejects empty audio files."""
    response = client.post(
        "/api/companion/transcribe",
        content=b"",
        headers={
            "Content-Type": "audio/webm",
            "X-Audio-Filename": "empty.webm",
        },
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_03_transcribe_unsupported_format():
    """Verify POST /api/companion/transcribe rejects unsupported file formats."""
    response = client.post(
        "/api/companion/transcribe",
        content=b"random text data",
        headers={
            "Content-Type": "text/plain",
            "X-Audio-Filename": "document.txt",
        },
    )
    assert response.status_code == 415
    assert "unsupported audio type" in response.json()["detail"].lower()


def test_04_transcribe_missing_api_key():
    """Verify POST /api/companion/transcribe returns 503 when API key is missing."""
    with patch("backend.app.companion.transcribe.GROQ_API_KEY", ""):
        response = client.post(
            "/api/companion/transcribe",
            content=b"audio_bytes",
            headers={
                "Content-Type": "audio/wav",
                "X-Audio-Filename": "speech.wav",
            },
        )
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()


def test_05_transcribe_groq_provider_error():
    """Verify POST /api/companion/transcribe handles Groq Whisper exceptions gracefully."""
    mock_groq_client = MagicMock()
    mock_groq_client.audio = MagicMock()
    mock_groq_client.audio.transcriptions = MagicMock()
    mock_groq_client.audio.transcriptions.create = AsyncMock(side_effect=RuntimeError("Groq API rate limit"))

    with patch("backend.app.companion.transcribe.get_async_groq_client", return_value=mock_groq_client), \
         patch("backend.app.companion.transcribe.GROQ_API_KEY", "mock_key"):
        response = client.post(
            "/api/companion/transcribe",
            content=b"audio_bytes",
            headers={
                "Content-Type": "audio/webm",
                "X-Audio-Filename": "speech.webm",
            },
        )
        assert response.status_code == 502
        assert "transcription service error" in response.json()["detail"].lower()


def test_06_transcribe_accurate_mode():
    """Verify X-Accuracy-Mode: accurate routes to whisper-large-v3."""
    mock_transcription = MagicMock()
    mock_transcription.text = "High accuracy transcription"

    mock_groq_client = MagicMock()
    mock_groq_client.audio = MagicMock()
    mock_groq_client.audio.transcriptions = MagicMock()
    mock_groq_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)

    with patch("backend.app.companion.transcribe.get_async_groq_client", return_value=mock_groq_client), \
         patch("backend.app.companion.transcribe.GROQ_API_KEY", "mock_key"):
        response = client.post(
            "/api/companion/transcribe",
            content=b"audio_bytes",
            headers={
                "Content-Type": "audio/webm",
                "X-Accuracy-Mode": "accurate",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "whisper-large-v3"
        assert data["transcript"] == "High accuracy transcription"


def test_07_tts_info_endpoint():
    """Verify GET /api/companion/tts/info returns Orpheus model metadata and female voices."""
    response = client.get("/api/companion/tts/info")
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "canopylabs/orpheus-v1-english"
    assert data["default_voice"] == "autumn"
    assert "autumn" in data["supported_voices"]
    assert "diana" in data["supported_voices"]
    assert "hannah" in data["supported_voices"]
    assert data["fallback"] == "web_speech"


def test_08_tts_synthesize_endpoint_fallback():
    """Verify POST /api/companion/synthesize handles fallback smoothly."""
    response = client.post(
        "/api/companion/synthesize",
        json={
            "text": "Hello there, I am Meli.",
            "voice": "autumn",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fallback"
    assert data["fallback"] == "web_speech"

