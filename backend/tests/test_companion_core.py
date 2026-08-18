"""
test_companion_core.py - Unit Test Suite for Meli Companion Intelligence Core

Tests:
1. Persona configuration and prompt construction
2. Structured companion event schema validation & SSE serialization
3. Memory selection rules (should_remember) & category classification
4. Context assembly (memories + enterprise facts + history + persona)
5. Companion orchestrator stream generation with mocked Groq
6. Error handling and graceful error event emission
7. FastAPI POST /api/companion/chat endpoint execution
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.companion.events import (
    CompanionEvent,
    create_thinking_event,
    create_memory_event,
    create_stream_event,
    create_completed_event,
    create_error_event,
)
from backend.app.companion.persona import (
    PersonaConfig,
    DEFAULT_PERSONA,
    build_persona_prompt,
)
from backend.app.companion.memory import (
    should_remember,
    MemoryDecision,
    MemoryItem,
)
from backend.app.companion.orchestrator import (
    assemble_companion_context,
    stream_companion_chat,
)


# ============================================================
# 1. Persona Engine Tests
# ============================================================

def test_01_persona_construction_defaults():
    """Verify default persona contains Meli core philosophy and tone."""
    persona = DEFAULT_PERSONA
    assert "Meli" in persona.identity
    assert "She doesn't demand attention. She earns it." == persona.core_principle
    assert "Warm" in persona.tone
    assert len(persona.interaction_principles) >= 3


def test_02_build_persona_prompt_compilation():
    """Verify persona compiles into complete system instruction with active context."""
    custom_ctx = "Recalled User Context:\n- Preparing an enterprise AI demo"
    prompt = build_persona_prompt(custom_instructions=custom_ctx)

    assert "Meli" in prompt
    assert "She doesn't demand attention. She earns it." in prompt
    assert "Preparing an enterprise AI demo" in prompt


# ============================================================
# 2. Structured Companion Event Schema Tests
# ============================================================

def test_03_companion_event_schemas_and_sse():
    """Verify event creation and SSE serialization formatted as data: {json}\\n\\n."""
    think_evt = create_thinking_event("Connecting thoughts...")
    assert think_evt.type == "THINKING"
    assert think_evt.visual_hint == "focused"

    sse_line = think_evt.to_sse_line()
    assert sse_line.startswith("data: ")
    assert sse_line.endswith("\n\n")

    parsed = json.loads(sse_line[6:].strip())
    assert parsed["type"] == "THINKING"
    assert parsed["visual_hint"] == "focused"

    stream_evt = create_stream_event("Hello")
    assert stream_evt.type == "RESPONSE_STREAM"
    assert stream_evt.token == "Hello"

    mem_evt = create_memory_event(2, "Recalled 2 items")
    assert mem_evt.type == "MEMORY_RETRIEVED"
    assert mem_evt.visual_hint == "curious"
    assert mem_evt.metadata["count"] == 2

    comp_evt = create_completed_event("Full response")
    assert comp_evt.type == "RESPONSE_COMPLETED"
    assert comp_evt.visual_hint == "happy"

    err_evt = create_error_event("Something broke")
    assert err_evt.type == "ERROR"
    assert err_evt.visual_hint == "nervous"


# ============================================================
# 3. Memory Selection Service Tests
# ============================================================

def test_04_memory_selection_salient_facts():
    """Verify should_remember detects project context, commitments, and preferences."""
    # Explicit command
    d1 = should_remember("Please remember that I am preparing an enterprise AI demo.")
    assert d1.should_store is True
    assert d1.category == "PROJECT_CONTEXT"

    # Project context
    d2 = should_remember("I am building a FastAPI backend with PostgreSQL.")
    assert d2.should_store is True
    assert d2.category == "PROJECT_CONTEXT"

    # User preference
    d3 = should_remember("I prefer dark mode and concise responses.")
    assert d3.should_store is True
    assert d3.category == "USER_PREFERENCE"

    # User commitment
    d4 = should_remember("I need to finish the sprint report by 5 PM.")
    assert d4.should_store is True
    assert d4.category == "USER_COMMITMENT"


def test_05_memory_selection_ignores_chitchat():
    """Verify should_remember ignores greetings, filler, and ephemeral questions."""
    assert should_remember("Hello Meli!").should_store is False
    assert should_remember("How are you today?").should_store is False
    assert should_remember("Thanks!").should_store is False
    assert should_remember("What is the weather like?").should_store is False
    assert should_remember("ok cool").should_store is False


# ============================================================
# 4. Context Assembly Tests
# ============================================================

def test_06_context_assembly_structure():
    """Verify memories, enterprise hits, and conversation history are structured cleanly."""
    memories = [
        MemoryItem(
            id="mem-1",
            fact="User is preparing an enterprise demo",
            category="PROJECT_CONTEXT",
            source_tier="episodic",
        )
    ]
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]

    messages = assemble_companion_context(
        user_message="What am I preparing?",
        memories=memories,
        enterprise_hits=[],
        history_messages=history,
    )

    assert len(messages) >= 4
    assert messages[0]["role"] == "system"
    assert "User is preparing an enterprise demo" in messages[0]["content"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "What am I preparing?"


# ============================================================
# 5. Orchestrator Streaming & API Tests
# ============================================================

@pytest.mark.asyncio
async def test_07_companion_orchestrator_mocked_stream():
    """Verify companion orchestrator executes full lifecycle: THINKING -> STREAM -> COMPLETED."""
    mock_chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello "))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="there!"))]),
    ]

    async def mock_stream_generator(*args, **kwargs):
        for chunk in mock_chunks:
            yield chunk

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_stream_generator)

    with patch("backend.app.companion.orchestrator.get_groq_client", return_value=mock_client):
        events = []
        async for sse_line in stream_companion_chat(
            user_message="What can you help me with?",
            history=[],
            session=None,
        ):
            if sse_line.startswith("data: "):
                data = json.loads(sse_line[6:].strip())
                events.append(data)

        types = [e["type"] for e in events]
        assert "THINKING" in types
        assert "RESPONSE_STREAM" in types
        assert "RESPONSE_COMPLETED" in types

        # Check full content accumulated
        streamed_tokens = "".join(e["token"] for e in events if e.get("token"))
        assert streamed_tokens == "Hello there!"


@pytest.mark.asyncio
async def test_08_companion_orchestrator_error_handling():
    """Verify companion orchestrator yields ERROR event on failure without crashing."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("Groq service timeout"))

    with patch("backend.app.companion.orchestrator.get_groq_client", return_value=mock_client):
        events = []
        async for sse_line in stream_companion_chat(
            user_message="Trigger error test",
            history=[],
            session=None,
        ):
            if sse_line.startswith("data: "):
                events.append(json.loads(sse_line[6:].strip()))

        types = [e["type"] for e in events]
        assert "THINKING" in types
        assert "ERROR" in types
        assert events[-1]["visual_hint"] == "nervous"


@pytest.mark.asyncio
async def test_09_companion_chat_fastapi_endpoint():
    """Verify POST /api/companion/chat endpoint returns 200 SSE stream."""
    mock_chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="I am Meli."))]),
    ]

    async def mock_stream_gen(*args, **kwargs):
        for chunk in mock_chunks:
            yield chunk

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_stream_gen)

    with patch("backend.app.companion.orchestrator.get_groq_client", return_value=mock_client):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/companion/chat",
                json={"message": "Who are you?", "top_k": 2},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
