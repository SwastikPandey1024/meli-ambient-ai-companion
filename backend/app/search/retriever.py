"""
retriever.py - Real BM25 Search Execution against Elasticsearch
"""

import time
import logging
from typing import List, Optional, Dict, Any
from elasticsearch import AsyncElasticsearch
from backend.app.config import ELASTICSEARCH_INDEX
from backend.app.schemas import SearchResultItem
from backend.app.search.client import get_es_client

logger = logging.getLogger("meli.elasticsearch.retriever")


async def execute_bm25_search(
    query: str,
    limit: int = 5,
    category: Optional[str] = None,
    client: Optional[AsyncElasticsearch] = None,
    index_name: Optional[str] = None,
) -> List[SearchResultItem]:
    """
    Execute multi-field BM25 full-text query with title boost in Elasticsearch.
    """
    es = client or get_es_client()
    if es is None:
        return []

    idx = index_name or ELASTICSEARCH_INDEX

    # Multi-match BM25 query with field weightings
    must_clauses: List[Dict[str, Any]] = [
        {
            "multi_match": {
                "query": query,
                "fields": ["title^3.0", "content^1.0", "category^1.5"],
                "type": "best_fields",
                "fuzziness": "AUTO",
            }
        }
    ]

    if category:
        must_clauses.append({"term": {"category": category}})

    body = {
        "size": limit,
        "query": {"bool": {"must": must_clauses}},
        "highlight": {
            "fields": {
                "content": {"fragment_size": 150, "number_of_fragments": 1},
                "title": {"fragment_size": 100, "number_of_fragments": 1},
            }
        },
    }

    try:
        response = await es.search(index=idx, body=body)
        hits = response.get("hits", {}).get("hits", [])

        results: List[SearchResultItem] = []
        for hit in hits:
            source = hit.get("_source", {})
            doc_id = hit.get("_id", source.get("id", ""))
            title = source.get("title", "Untitled Document")
            content = source.get("content", "")
            cat = source.get("category", "general")
            src = source.get("source", "internal_kb")
            score = float(hit.get("_score", 0.0))

            # Extract highlight snippet if available
            highlights = hit.get("highlight", {})
            if "content" in highlights and highlights["content"]:
                snippet = highlights["content"][0]
            elif "title" in highlights and highlights["title"]:
                snippet = highlights["title"][0]
            else:
                snippet = content[:180] + ("..." if len(content) > 180 else "")

            results.append(
                SearchResultItem(
                    id=doc_id,
                    title=title,
                    content=content,
                    snippet=snippet,
                    category=cat,
                    source=src,
                    score=round(score, 3),
                    source_type="elasticsearch",
                )
            )

        return results

    except Exception as e:
        logger.error(f"Elasticsearch BM25 search failed: {e}")
        return []
