"""
seed.py - Small Coherent Enterprise Knowledge Dataset and Ingestion Script
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running as direct script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
import logging
from typing import List, Dict, Any

from backend.app.database import get_engine, init_db, get_session_factory
from backend.app.repositories.enterprise_record_repo import EnterpriseRecordRepository
from backend.app.search.client import get_es_client, close_es_client
from backend.app.search.indexer import bulk_seed_documents

logger = logging.getLogger("meli.seed")

# Coherent Enterprise Seed Dataset
ENTERPRISE_SEED_DATA: List[Dict[str, Any]] = [
    {
        "id": "doc-meli-arch-001",
        "title": "Meli Companion Architecture & Philosophy",
        "category": "architecture",
        "source": "design_doc",
        "author": "Core Engineering Team",
        "content": (
            "Meli is designed as an ambient AI desktop companion that stays with the user throughout their workday. "
            "Her interaction model operates on three principles: subtle micro-motions, non-intrusive ambient presence, "
            "and grounded intelligence. Meli's chest houses the Signal Heart at canonical coordinates X: 50.67%, Y: 36.04%. "
            "Her state transitions progress from IDLE (pink) -> THINKING (violet) -> COMPLETE (green settling to pink). "
            "Phase 0 animations are locked with strict motion limits to preserve visual comfort."
        ),
    },
    {
        "id": "doc-incident-sla-002",
        "title": "Engineering Incident Response SLA Policy",
        "category": "operations",
        "source": "handbook",
        "author": "Site Reliability Engineering",
        "content": (
            "Our company enforces strict SLA tiers for engineering production incidents:\n"
            "- Severity 1 (Critical Outage / Data Loss): Response time < 15 minutes, 24/7 on-call paging, executive notification within 30 minutes.\n"
            "- Severity 2 (Degraded Core Service): Response time < 1 hour during business hours, daily updates.\n"
            "- Severity 3 (Minor Bug / UX Glitch): Response time < 24 hours, resolved in next sprint cycle.\n"
            "All Sev-1 and Sev-2 incidents require a blameless post-mortem document completed within 48 hours."
        ),
    },
    {
        "id": "doc-security-policy-003",
        "title": "Enterprise Security & Secret Protection Standard",
        "category": "security",
        "source": "security_standard",
        "author": "Information Security Office",
        "content": (
            "Strict zero-trust security controls apply across all frontend and backend services:\n"
            "1. API keys (Groq, OpenAI, Cloud credentials) must NEVER be exposed in frontend JavaScript bundles or client-side responses.\n"
            "2. All database connections must use TLS encryption and connection pooling.\n"
            "3. Sensitive environment variables reside exclusively in server-side .env or AWS Secrets Manager.\n"
            "4. Audit logs are permanently recorded in PostgreSQL for all enterprise query and RAG operations."
        ),
    },
    {
        "id": "doc-workplace-policy-004",
        "title": "Remote Workplace & Equipment Policy",
        "category": "hr_policy",
        "source": "people_operations",
        "author": "People Operations",
        "content": (
            "All full-time employees are provided with standard enterprise hardware and stipends:\n"
            "- Annual Home Office Stipend: $1,200 per calendar year for ergonomics, monitors, and peripherals.\n"
            "- Hardware Refresh: Company laptops are refreshed every 36 months.\n"
            "- Health & Wellness Allowance: $100 per month reimburseable for fitness, ergonomics, and mental wellness.\n"
            "- Core Collaboration Hours: 10:00 AM to 4:00 PM in the employee's designated local timezone."
        ),
    },
]


async def seed_all_enterprise_data() -> Dict[str, Any]:
    """Seed enterprise data into both PostgreSQL and Elasticsearch."""
    results = {"postgresql_records": 0, "elasticsearch_docs": 0, "errors": []}

    # 1. Seed into PostgreSQL
    engine = get_engine()
    if engine is not None:
        try:
            await init_db(engine)
            session_factory = get_session_factory()
            if session_factory:
                async with session_factory() as session:
                    repo = EnterpriseRecordRepository(session)
                    for item in ENTERPRISE_SEED_DATA:
                        existing = await repo.get_by_id(item["id"])
                        if not existing:
                            await repo.create_record(
                                record_id=item["id"],
                                title=item["title"],
                                content=item["content"],
                                category=item["category"],
                                source=item["source"],
                                author=item.get("author"),
                            )
                            results["postgresql_records"] += 1
                        else:
                            results["postgresql_records"] += 1
                    await session.commit()
                logger.info(f"PostgreSQL verified with {results['postgresql_records']} records.")
        except Exception as e:
            logger.warning(f"PostgreSQL seeding failed: {e}")
            results["errors"].append(f"PostgreSQL: {str(e)}")
    else:
        results["errors"].append("PostgreSQL: not configured or unavailable")

    # 2. Seed into Elasticsearch
    es_client = get_es_client()
    if es_client is not None:
        try:
            count = await bulk_seed_documents(ENTERPRISE_SEED_DATA, client=es_client)
            results["elasticsearch_docs"] = count
            logger.info(f"Elasticsearch verified with {count} documents.")
        except Exception as e:
            logger.warning(f"Elasticsearch seeding failed: {e}")
            results["errors"].append(f"Elasticsearch: {str(e)}")
        finally:
            await close_es_client()
    else:
        results["errors"].append("Elasticsearch: not configured or unavailable")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = asyncio.run(seed_all_enterprise_data())
    print("Seed Results:", res)
