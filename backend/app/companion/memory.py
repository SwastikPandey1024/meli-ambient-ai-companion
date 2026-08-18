"""
memory.py - 3-Tier Memory Foundation & Memory Selection Service for Meli
"""

import re
import logging
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models import EnterpriseRecord
from backend.app.search.indexer import index_document
from backend.app.search.retriever import execute_bm25_search

logger = logging.getLogger("meli.companion.memory")

MemoryCategory = Literal[
    "USER_PREFERENCE",
    "USER_COMMITMENT",
    "PROJECT_CONTEXT",
    "IMPORTANT_EVENT",
    "GENERAL_FACT",
]


class MemoryDecision(BaseModel):
    """Result of memory selection decision."""
    should_store: bool
    category: Optional[MemoryCategory] = None
    extracted_fact: Optional[str] = None
    confidence: float = 0.0
    reason: str = "No salient memory patterns detected"


class MemoryItem(BaseModel):
    """Retrieved memory fact."""
    id: str
    fact: str
    category: str
    source_tier: Literal["short_term", "episodic", "semantic"]
    score: float = 1.0
    created_at: Optional[datetime] = None


# Heuristic patterns for memory detection
MEMORY_TRIGGER_PATTERNS = [
    # Explicit commands
    (r"(?:please\s+)?(?:remember\s+that|remember|don't\s+forget\s+that|note\s+that|keep\s+in\s+mind\s+that)\s+(.+)", "PROJECT_CONTEXT", 0.95),
    # Project / Task context
    (r"(?:i\s+am|i'm)\s+(?:working\s+on|preparing|building|developing|designing|architecting)\s+(.+)", "PROJECT_CONTEXT", 0.85),
    # Preferences
    (r"(?:i\s+prefer|i\s+like|my\s+favorite|always\s+use|call\s+me)\s+(.+)", "USER_PREFERENCE", 0.85),
    # Commitments & Deadlines
    (r"(?:i\s+need\s+to|i\s+have\s+to|i\s+must|my\s+deadline\s+is|i\s+promised\s+to)\s+(.+)", "USER_COMMITMENT", 0.80),
    # Important events
    (r"(?:tomorrow\s+is|today\s+we|next\s+week\s+is|we\s+are\s+launching)\s+(.+)", "IMPORTANT_EVENT", 0.80),
]

# Noise / Chit-chat patterns to strictly ignore
IGNORE_PATTERNS = [
    r"^(?:hi|hello|hey|good\s+morning|good\s+evening|good\s+night|yo|meli)\b",
    r"^(?:how\s+are\s+you|what's\s+up|how's\s+it\s+going|what\s+can\s+you\s+do|who\s+are\s+you)\b",
    r"^(?:thanks|thank\s+you|ok|okay|cool|nice|got\s+it|sure|great|bye|see\s+ya)\b",
    r"^(?:what\s+is|search\s+for|tell\s+me\s+about|calculate|help)\b",
]


def should_remember(message: str, context: Optional[Dict[str, Any]] = None) -> MemoryDecision:
    """
    Evaluate whether a user message contains a durable fact that should be stored.
    Filters out transient chit-chat, ephemeral queries, and greetings.
    """
    clean_text = message.strip()
    if len(clean_text) < 5:
        return MemoryDecision(should_store=False, reason="Message too short")

    # Check ignore list
    lower_text = clean_text.lower()
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, lower_text):
            return MemoryDecision(
                should_store=False,
                reason="Transient conversation or generic query ignored"
            )

    # Check salient memory patterns
    for pattern, category, confidence in MEMORY_TRIGGER_PATTERNS:
        match = re.search(pattern, lower_text, re.IGNORECASE)
        if match:
            extracted = clean_text[match.start(1):].strip() if match.groups() else clean_text
            # Clean up trailing punctuation
            extracted = extracted.rstrip(".!?")
            return MemoryDecision(
                should_store=True,
                category=category,  # type: ignore
                extracted_fact=clean_text,  # Keep full contextual sentence for grounding
                confidence=confidence,
                reason=f"Matched pattern for {category}",
            )

    return MemoryDecision(
        should_store=False,
        reason="No durable user facts or commitments detected",
    )


async def store_episodic_memory(
    decision: MemoryDecision,
    session: Optional[AsyncSession] = None,
    user_id: str = "default_user",
) -> Optional[str]:
    """
    Store an accepted memory fact into PostgreSQL and index in Elasticsearch.
    """
    if not decision.should_store or not decision.extracted_fact:
        return None

    fact_content = decision.extracted_fact
    category_name = f"memory:{decision.category or 'GENERAL_FACT'}".lower()
    title_snippet = fact_content[:60] + ("..." if len(fact_content) > 60 else "")

    record_id = None
    if session is not None:
        try:
            record = EnterpriseRecord(
                title=f"User Fact: {title_snippet}",
                category=category_name,
                content=fact_content,
                source="companion_memory",
                author=user_id,
            )
            session.add(record)
            await session.flush()
            record_id = record.id
            logger.info(f"Stored episodic memory in PostgreSQL: {record_id} ({category_name})")
        except Exception as e:
            logger.warning(f"Failed to persist memory to PostgreSQL: {e}")

    # Index into Elasticsearch for semantic search
    try:
        if record_id:
            await index_document(
                doc_id=record_id,
                title=f"User Fact: {title_snippet}",
                content=fact_content,
                category=category_name,
                source="companion_memory",
                metadata={"user_id": user_id, "category": decision.category},
            )
            logger.info(f"Indexed episodic memory in Elasticsearch: {record_id}")
    except Exception as e:
        logger.debug(f"Elasticsearch memory indexing skipped or failed: {e}")

    return record_id


async def retrieve_memories(
    query: str,
    session: Optional[AsyncSession] = None,
    top_k: int = 3,
) -> List[MemoryItem]:
    """
    Retrieve relevant episodic and semantic memories for the active conversation.
    """
    memories: List[MemoryItem] = []
    seen_facts = set()

    # 1. Query Elasticsearch for semantic match in memory categories
    try:
        search_hits = await execute_bm25_search(query=query, limit=top_k)
        for hit in search_hits:
            if "memory" in hit.category.lower() or hit.source == "companion_memory":
                if hit.content not in seen_facts:
                    memories.append(
                        MemoryItem(
                            id=hit.id,
                            fact=hit.content,
                            category=hit.category,
                            source_tier="semantic",
                            score=hit.score,
                        )
                    )
                    seen_facts.add(hit.content)
    except Exception as e:
        logger.debug(f"Elasticsearch memory search unavailable: {e}")

    # 2. Query PostgreSQL episodic memory records directly
    if session is not None and len(memories) < top_k:
        try:
            stmt = (
                select(EnterpriseRecord)
                .where(EnterpriseRecord.source == "companion_memory")
                .order_by(EnterpriseRecord.created_at.desc())
                .limit(top_k * 2)
            )
            result = await session.execute(stmt)
            records = result.scalars().all()

            # Simple keyword matching across query tokens
            q_words = set(query.lower().split())
            for rec in records:
                if rec.content not in seen_facts:
                    rec_words = set(rec.content.lower().split())
                    overlap = len(q_words.intersection(rec_words))
                    if overlap > 0 or len(records) <= 2:
                        memories.append(
                            MemoryItem(
                                id=rec.id,
                                fact=rec.content,
                                category=rec.category,
                                source_tier="episodic",
                                score=1.0 + overlap * 0.5,
                                created_at=rec.created_at,
                            )
                        )
                        seen_facts.add(rec.content)
        except Exception as e:
            logger.debug(f"PostgreSQL episodic memory query failed: {e}")

    # Sort by relevance score
    memories.sort(key=lambda m: m.score, reverse=True)
    return memories[:top_k]
