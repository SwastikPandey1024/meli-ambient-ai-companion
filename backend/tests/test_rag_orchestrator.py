"""
test_rag_orchestrator.py - Unit and Integration Tests for RAG Orchestrator
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.rag_orchestrator import (
    retrieve_enterprise_context,
    build_grounded_messages,
    stream_enterprise_rag_chat,
)
from backend.app.schemas import SearchResultItem


def test_build_grounded_messages_structure():
    """Verify prompt formatting strictly separates enterprise evidence."""
    context = "[Doc: SLA Policy]\nSev-1 response time is 15 minutes."
    user_query = "What is the Sev-1 response time?"
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]

    messages = build_grounded_messages(
        user_query=user_query,
        context=context,
        conversation_history=history,
    )

    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert "# ENTERPRISE EVIDENCE" in messages[0]["content"]
    assert "Sev-1 response time is 15 minutes" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == user_query


@pytest.mark.asyncio
async def test_retrieve_enterprise_context_merging():
    """Test merging results from both Elasticsearch and PostgreSQL."""
    mock_es_results = [
        SearchResultItem(
            id="doc-es-1",
            title="Incident Policy",
            content="Sev-1 response under 15m",
            snippet="Sev-1 response...",
            category="operations",
            source="handbook",
            score=3.5,
        )
    ]

    with patch("backend.app.rag_orchestrator.execute_bm25_search", return_value=mock_es_results):
        citations, formatted = await retrieve_enterprise_context(
            query="incident SLA",
            top_k=2,
            db_session=None,
        )

        assert len(citations) == 1
        assert citations[0].title == "Incident Policy"
        assert citations[0].source_type == "elasticsearch"
        assert "[Doc: Incident Policy]" in formatted


@pytest.mark.asyncio
async def test_stream_enterprise_rag_chat_execution():
    """Test full RAG streaming generator with mocked Groq client."""
    mock_citations = [
        SearchResultItem(
            id="doc-1",
            title="Meli Architecture",
            content="Meli Signal Heart is at 50.67%, 36.04%.",
            snippet="Signal Heart...",
            category="architecture",
            source="design_doc",
            score=5.0,
        )
    ]

    # Create mock Groq async stream chunks
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock(delta=MagicMock(content="Meli's "))]
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock(delta=MagicMock(content="Signal Heart."))]

    async def mock_chunks():
        yield chunk1
        yield chunk2

    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_chunks())

    with patch("backend.app.rag_orchestrator.execute_bm25_search", return_value=mock_citations):
        events = []
        async for sse in stream_enterprise_rag_chat(
            user_message="Where is the Signal Heart?",
            groq_client=mock_groq_client,
            model="llama-3.3-70b-versatile",
        ):
            events.append(sse)

        assert len(events) >= 3
        # First event is citations metadata
        assert "citations" in events[0]
        assert "Meli Architecture" in events[0]

        # Subsequent events are streamed tokens
        joined_stream = "".join(events)
        assert "Meli's " in joined_stream
        assert "Signal Heart." in joined_stream
        assert "[DONE]" in joined_stream
