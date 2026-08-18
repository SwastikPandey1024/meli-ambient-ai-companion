"""
client.py - Official AsyncElasticsearch Client Initialization
"""

import logging
from typing import Optional
from elasticsearch import AsyncElasticsearch
from backend.app.config import ELASTICSEARCH_URL, ELASTICSEARCH_API_KEY

logger = logging.getLogger("meli.elasticsearch")

_es_client: Optional[AsyncElasticsearch] = None


def get_es_client() -> Optional[AsyncElasticsearch]:
    """Get or create singleton AsyncElasticsearch client."""
    global _es_client
    if _es_client is not None:
        return _es_client

    if not ELASTICSEARCH_URL:
        return None

    try:
        kwargs = {}
        if ELASTICSEARCH_API_KEY:
            kwargs["api_key"] = ELASTICSEARCH_API_KEY

        # Handle local http vs remote https
        if ELASTICSEARCH_URL.startswith("http://"):
            kwargs["verify_certs"] = False

        _es_client = AsyncElasticsearch(
            hosts=[ELASTICSEARCH_URL],
            request_timeout=10,
            max_retries=2,
            retry_on_timeout=True,
            **kwargs,
        )
        logger.info("AsyncElasticsearch client initialized.")
        return _es_client
    except Exception as e:
        logger.error(f"Failed to initialize Elasticsearch client: {e}")
        return None


async def close_es_client():
    """Gracefully close Elasticsearch client."""
    global _es_client
    if _es_client is not None:
        await _es_client.close()
        _es_client = None
