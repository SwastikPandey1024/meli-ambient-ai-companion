"""
Search package for Elasticsearch BM25 retrieval
"""
from backend.app.search.client import get_es_client
from backend.app.search.health import check_elasticsearch_health
from backend.app.search.indexer import index_document, bulk_seed_documents
from backend.app.search.retriever import execute_bm25_search
from backend.app.search.index_manager import ensure_index_exists

__all__ = [
    "get_es_client",
    "check_elasticsearch_health",
    "index_document",
    "bulk_seed_documents",
    "execute_bm25_search",
    "ensure_index_exists",
]
