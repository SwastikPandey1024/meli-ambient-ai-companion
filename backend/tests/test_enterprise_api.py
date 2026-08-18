"""
test_enterprise_api.py - Integration and Route Contract Tests for FastAPI
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.main import app
from backend.app.schemas import ComponentHealth


@pytest.mark.asyncio
async def test_legacy_health_endpoint():
    """Verify Phase 1A /api/health endpoint contract remains intact."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "model_configured" in data
        assert "groq_api_key_configured" in data


@pytest.mark.asyncio
async def test_enterprise_status_endpoint():
    """Verify GET /api/enterprise/status reports real states for PG, ES, and Groq."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/enterprise/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "postgresql" in data
        assert "elasticsearch" in data
        assert "groq" in data
        assert data["postgresql"]["state"] in ("connected", "unavailable", "not_configured")
        assert data["elasticsearch"]["state"] in ("connected", "unavailable", "not_configured")
        assert data["groq"]["state"] in ("connected", "unavailable", "not_configured")


@pytest.mark.asyncio
async def test_enterprise_search_endpoint():
    """Verify POST /api/enterprise/search route contract with mocked search results."""
    from backend.app.schemas import SearchResultItem

    mock_results = [
        SearchResultItem(
            id="doc-1",
            title="Incident SLA",
            content="Sev-1 response time < 15 min.",
            snippet="Sev-1 response time...",
            category="operations",
            source="handbook",
            score=4.2,
        )
    ]

    with patch("backend.app.main.execute_bm25_search", return_value=mock_results):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/enterprise/search",
                json={"query": "Sev-1 SLA", "limit": 5},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["results"][0]["title"] == "Incident SLA"
            assert "latency_ms" in data


@pytest.mark.asyncio
async def test_enterprise_chat_streaming_endpoint():
    """Verify POST /api/enterprise/chat SSE stream returns events."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/enterprise/chat",
            json={"message": "What is the policy for incident response?", "top_k": 2},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
