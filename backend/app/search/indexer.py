"""
indexer.py - Document Ingestion and Indexing into Elasticsearch
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from elasticsearch import AsyncElasticsearch
from backend.app.config import ELASTICSEARCH_INDEX
from backend.app.search.client import get_es_client
from backend.app.search.index_manager import ensure_index_exists

logger = logging.getLogger("meli.elasticsearch.indexer")


async def index_document(
    title: str,
    content: str,
    category: str = "general",
    source: str = "internal_kb",
    author: Optional[str] = None,
    doc_id: Optional[str] = None,
    client: Optional[AsyncElasticsearch] = None,
    index_name: Optional[str] = None,
) -> Optional[str]:
    """Index single enterprise document into Elasticsearch."""
    es = client or get_es_client()
    if es is None:
        return None

    idx = index_name or ELASTICSEARCH_INDEX
    await ensure_index_exists(es, idx)

    actual_id = doc_id or str(uuid.uuid4())
    doc_body = {
        "id": actual_id,
        "title": title,
        "content": content,
        "category": category,
        "source": source,
        "author": author,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        await es.index(index=idx, id=actual_id, document=doc_body, refresh="wait_for")
        logger.info(f"Indexed document '{title}' ({actual_id}) into Elasticsearch.")
        return actual_id
    except Exception as e:
        logger.error(f"Failed to index document '{title}': {e}")
        return None


async def bulk_seed_documents(
    documents: List[Dict[str, Any]],
    client: Optional[AsyncElasticsearch] = None,
    index_name: Optional[str] = None,
) -> int:
    """Seed multiple enterprise knowledge documents."""
    es = client or get_es_client()
    if es is None:
        return 0

    idx = index_name or ELASTICSEARCH_INDEX
    await ensure_index_exists(es, idx)

    count = 0
    for doc in documents:
        res = await index_document(
            title=doc["title"],
            content=doc["content"],
            category=doc.get("category", "general"),
            source=doc.get("source", "seed_data"),
            author=doc.get("author", "system"),
            doc_id=doc.get("id"),
            client=es,
            index_name=idx,
        )
        if res:
            count += 1
    return count
