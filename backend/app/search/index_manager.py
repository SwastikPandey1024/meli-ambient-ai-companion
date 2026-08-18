"""
index_manager.py - Elasticsearch Index Schema and Mapping Definition
"""

import logging
from typing import Optional
from elasticsearch import AsyncElasticsearch
from backend.app.config import ELASTICSEARCH_INDEX
from backend.app.search.client import get_es_client

logger = logging.getLogger("meli.elasticsearch.index")

# Explicit BM25 Enterprise Document Mapping compatible with Serverless & Standard Elasticsearch
ENTERPRISE_INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "enterprise_text_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"],
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "enterprise_text_analyzer",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
            },
            "content": {
                "type": "text",
                "analyzer": "enterprise_text_analyzer",
            },
            "category": {"type": "keyword"},
            "source": {"type": "keyword"},
            "author": {"type": "keyword"},
            "created_at": {"type": "date"},
        }
    },
}


async def ensure_index_exists(client: Optional[AsyncElasticsearch] = None, index_name: Optional[str] = None) -> bool:
    """Ensure target Elasticsearch index exists with defined BM25 mapping."""
    es = client or get_es_client()
    if es is None:
        return False

    idx = index_name or ELASTICSEARCH_INDEX
    try:
        exists = await es.indices.exists(index=idx)
        if not exists:
            logger.info(f"Creating Elasticsearch index '{idx}' with BM25 mapping...")
            await es.indices.create(index=idx, body=ENTERPRISE_INDEX_MAPPING)
            logger.info(f"Elasticsearch index '{idx}' created successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to verify/create Elasticsearch index '{idx}': {e}")
        return False
