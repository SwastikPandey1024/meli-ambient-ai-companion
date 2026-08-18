"""
test_enterprise_search.py - Unit and Integration Tests for Elasticsearch Layer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.search.health import check_elasticsearch_health
from backend.app.search.index_manager import ensure_index_exists, ENTERPRISE_INDEX_MAPPING
from backend.app.search.indexer import index_document, bulk_seed_documents
from backend.app.search.retriever import execute_bm25_search


def test_index_mapping_structure():
    """Verify BM25 index mapping schema definition."""
    assert "properties" in ENTERPRISE_INDEX_MAPPING["mappings"]
    props = ENTERPRISE_INDEX_MAPPING["mappings"]["properties"]
    assert "title" in props
    assert "content" in props
    assert "category" in props
    assert "source" in props
    assert props["title"]["type"] == "text"
    assert props["content"]["type"] == "text"


@pytest.mark.asyncio
async def test_elasticsearch_health_not_configured():
    """When ELASTICSEARCH_URL is empty, health check reports 'not_configured'."""
    with patch("backend.app.search.health.ELASTICSEARCH_URL", ""):
        health = await check_elasticsearch_health()
        assert health.state == "not_configured"
        assert "not set" in (health.details or "")


@pytest.mark.asyncio
async def test_elasticsearch_health_unavailable_on_failure():
    """When ping fails, health check reports 'unavailable'."""
    with patch("backend.app.search.health.ELASTICSEARCH_URL", "https://mock-es:9200"):
        with patch("backend.app.search.health.get_es_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ping.side_effect = ConnectionError("Could not reach host")
            mock_get_client.return_value = mock_client

            health = await check_elasticsearch_health()
            assert health.state == "unavailable"
            assert "Could not reach host" in (health.details or "")


@pytest.mark.asyncio
async def test_elasticsearch_health_connected():
    """When ping and info succeed, health check reports 'connected'."""
    with patch("backend.app.search.health.ELASTICSEARCH_URL", "https://mock-es:9200"):
        with patch("backend.app.search.health.get_es_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.info.return_value = {
                "cluster_name": "meli-enterprise-cluster",
                "version": {"number": "8.12.0"},
            }
            mock_get_client.return_value = mock_client

            health = await check_elasticsearch_health()
            assert health.state == "connected"
            assert "meli-enterprise-cluster" in (health.details or "")
            assert health.latency_ms is not None


@pytest.mark.asyncio
async def test_execute_bm25_search_parsing():
    """Test BM25 search query formatting and hit normalization."""
    mock_client = AsyncMock()
    mock_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": "doc-001",
                    "_score": 4.85,
                    "_source": {
                        "id": "doc-001",
                        "title": "Engineering Incident SLA Policy",
                        "content": "Sev-1 incident response time < 15 minutes.",
                        "category": "operations",
                        "source": "handbook",
                    },
                    "highlight": {
                        "content": ["<mark>Sev-1 incident response time</mark> < 15 minutes."]
                    },
                }
            ]
        }
    }

    results = await execute_bm25_search(
        query="Sev-1 response time",
        limit=5,
        client=mock_client,
        index_name="test_index",
    )

    assert len(results) == 1
    assert results[0].id == "doc-001"
    assert results[0].title == "Engineering Incident SLA Policy"
    assert results[0].score == 4.85
    assert results[0].source_type == "elasticsearch"
    assert "<mark>" in results[0].snippet


@pytest.mark.asyncio
async def test_index_document_execution():
    """Test document indexing into Elasticsearch."""
    mock_client = AsyncMock()
    mock_client.indices.exists.return_value = True
    mock_client.index.return_value = {"result": "created"}

    doc_id = await index_document(
        title="Security Guidelines",
        content="Never expose API keys.",
        category="security",
        doc_id="sec-101",
        client=mock_client,
        index_name="test_index",
    )

    assert doc_id == "sec-101"
    mock_client.index.assert_called_once()
