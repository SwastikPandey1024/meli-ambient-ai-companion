"""
health.py - Real Elasticsearch Cluster Connectivity and Health Check
"""

import time
import logging
from backend.app.config import ELASTICSEARCH_URL
from backend.app.schemas import ComponentHealth
from backend.app.search.client import get_es_client

logger = logging.getLogger("meli.elasticsearch.health")


async def check_elasticsearch_health() -> ComponentHealth:
    """
    Perform a real ping and cluster info check against Elasticsearch.
    Never reports 'connected' unless a real cluster response is received.
    """
    if not ELASTICSEARCH_URL:
        return ComponentHealth(
            state="not_configured",
            details="ELASTICSEARCH_URL environment variable is not set.",
        )

    es = get_es_client()
    if es is None:
        return ComponentHealth(
            state="unavailable",
            details="Could not initialize AsyncElasticsearch client.",
        )

    t0 = time.perf_counter()
    try:
        is_alive = await es.ping()
        latency = (time.perf_counter() - t0) * 1000.0

        if is_alive:
            info = await es.info()
            cluster_name = info.get("cluster_name", "unknown")
            es_version = info.get("version", {}).get("number", "unknown")
            return ComponentHealth(
                state="connected",
                details=f"Connected to cluster '{cluster_name}' (v{es_version}).",
                latency_ms=round(latency, 2),
            )
        else:
            return ComponentHealth(
                state="unavailable",
                details="Elasticsearch ping returned False.",
                latency_ms=round(latency, 2),
            )

    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000.0
        logger.warning(f"Elasticsearch health check failed: {type(e).__name__} - {e}")
        return ComponentHealth(
            state="unavailable",
            details=f"Connection failed ({type(e).__name__}): {str(e)}",
            latency_ms=round(latency, 2),
        )
