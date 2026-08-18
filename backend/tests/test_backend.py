"""
test_backend.py - Unit and Integration Tests for Meli FastAPI & Groq Backend
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import GROQ_MODEL
from backend.app.groq_client import (
    get_async_groq_client,
    format_messages,
    stream_groq_chat,
    generate_groq_chat,
)

client = TestClient(app)


def test_01_health_endpoint():
    """Verify GET /api/health returns 200 OK and expected structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["model_configured"] == GROQ_MODEL
    assert "groq_api_key_configured" in data


def test_02_chat_request_validation():
    """Verify POST /api/chat validates empty or missing fields."""
    # Empty payload
    response = client.post("/api/chat", json={})
    assert response.status_code == 422

    # Empty string message
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


def test_03_format_messages_includes_system_persona():
    """Ensure system prompt and conversation history are formatted properly."""
    messages = format_messages(
        user_message="Hello Meli",
        history=[{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hey there"}],
    )
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert "Meli" in messages[0]["content"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Hello Meli"


def test_04_missing_api_key_initialization():
    """Verify get_async_groq_client returns None when API key is missing."""
    assert get_async_groq_client(api_key="") is None


@pytest.mark.asyncio
async def test_05_mocked_groq_non_streaming_chat():
    """Verify non-streaming chat with a mocked AsyncGroq client."""
    mock_choice = MagicMock()
    mock_choice.message.content = "I'm Meli, your companion."
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 15
    mock_usage.completion_tokens = 8
    mock_usage.total_tokens = 23

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

    res = await generate_groq_chat("Hello", client=mock_client)
    assert res["reply"] == "I'm Meli, your companion."
    assert res["state"] == "COMPLETE"
    assert res["usage"]["total_tokens"] == 23


@pytest.mark.asyncio
async def test_06_mocked_groq_streaming_chat():
    """Verify token streaming with a mocked AsyncGroq client."""

    async def mock_stream_chunks():
        tokens = ["I'm ", "here ", "to ", "help."]
        for t in tokens:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = t
            yield chunk

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_stream_chunks())

    events = []
    async for event in stream_groq_chat("Hello", client=mock_client):
        events.append(event)

    assert len(events) >= 5
    assert "data: [DONE]\n\n" in events[-1]

    # Verify streamed payload tokens
    token_str = ""
    for ev in events:
        if ev.startswith("data: ") and not ev.startswith("data: [DONE]"):
            data = json.loads(ev[6:].strip())
            if "token" in data:
                token_str += data["token"]

    assert token_str == "I'm here to help."


@pytest.mark.asyncio
async def test_07_error_handling_graceful_fallback():
    """Verify graceful response when Groq raises an exception."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("Groq network timeout"))

    res = await generate_groq_chat("Hello", client=mock_client)
    assert res["state"] == "ERROR"
    assert "trouble reaching my thinking space" in res["reply"]
