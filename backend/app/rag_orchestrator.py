"""
rag_orchestrator.py - Grounded Enterprise RAG Pipeline (PostgreSQL + Elasticsearch + Groq)
"""

import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from groq import AsyncGroq

from backend.app.config import GROQ_MODEL, MELI_SYSTEM_PROMPT
from backend.app.groq_client import get_async_groq_client
from backend.app.schemas import CitationSource, SearchResultItem
from backend.app.search.retriever import execute_bm25_search
from backend.app.repositories.conversation_repo import ConversationRepository
from backend.app.repositories.enterprise_record_repo import EnterpriseRecordRepository
from backend.app.repositories.audit_repo import AuditRepository

logger = logging.getLogger("meli.rag")


async def retrieve_enterprise_context(
    query: str,
    top_k: int = 4,
    db_session: Optional[AsyncSession] = None,
) -> Tuple[List[CitationSource], str]:
    """
    Retrieve authoritative facts from PostgreSQL and relevant documents from Elasticsearch.
    """
    citations: List[CitationSource] = []
    context_blocks: List[str] = []

    # 1. Retrieve from Elasticsearch (BM25 full-text search)
    es_results: List[SearchResultItem] = await execute_bm25_search(query=query, limit=top_k)
    for res in es_results:
        citations.append(
            CitationSource(
                id=res.id,
                title=res.title,
                source=res.source,
                snippet=res.snippet,
                source_type="elasticsearch",
            )
        )
        context_blocks.append(
            f"[Doc: {res.title}] (Category: {res.category}, Source: {res.source})\n{res.content}"
        )

    # 2. Retrieve from PostgreSQL (Structured Knowledge Records) if session available
    if db_session is not None:
        try:
            record_repo = EnterpriseRecordRepository(db_session)
            pg_records = await record_repo.find_matching_records(query=query, limit=top_k)
            for rec in pg_records:
                citations.append(
                    CitationSource(
                        id=rec.id,
                        title=rec.title,
                        source=rec.source,
                        snippet=rec.content[:180] + ("..." if len(rec.content) > 180 else ""),
                        source_type="postgresql",
                    )
                )
                context_blocks.append(
                    f"[Record: {rec.title}] (Category: {rec.category}, Author: {rec.author or 'Unknown'})\n{rec.content}"
                )
        except Exception as e:
            logger.warning(f"PostgreSQL context retrieval exception: {e}")

    if not context_blocks:
        formatted_context = "No relevant enterprise evidence found in PostgreSQL or Elasticsearch for this query."
    else:
        formatted_context = "\n\n---\n\n".join(context_blocks)

    return citations, formatted_context


def build_grounded_messages(
    user_query: str,
    context: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, str]]:
    """Assemble grounded prompt with strict evidence separation."""
    grounded_system_prompt = f"""{MELI_SYSTEM_PROMPT}

# ENTERPRISE EVIDENCE (Retrieved from PostgreSQL & Elasticsearch):
{context}

# STRICT GROUNDING DIRECTIVES:
1. Answer the user's question using the provided ENTERPRISE EVIDENCE above.
2. Clearly cite the document/record title when referencing facts (e.g. "[Doc: Engineering Policy]").
3. If the evidence does NOT contain the answer, politely and clearly state: "I don't have that documented in our enterprise knowledge base."
4. Do NOT hallucinate policies, numbers, or internal details outside the provided evidence.
"""

    messages: List[Dict[str, str]] = [{"role": "system", "content": grounded_system_prompt}]

    if conversation_history:
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_query})
    return messages


async def stream_enterprise_rag_chat(
    user_message: str,
    conversation_id: Optional[str] = None,
    top_k: int = 4,
    db_session: Optional[AsyncSession] = None,
    groq_client: Optional[AsyncGroq] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Execute full Enterprise RAG pipeline and stream token-by-token SSE response.
    """
    client = groq_client or get_async_groq_client()
    groq_model = model or GROQ_MODEL

    from backend.app.database import get_session_factory

    session = db_session
    close_session_on_exit = False
    if session is None:
        factory = get_session_factory()
        if factory:
            session = factory()
            close_session_on_exit = True

    # Step 1: Retrieve context from PostgreSQL & Elasticsearch
    citations, context = await retrieve_enterprise_context(
        query=user_message, top_k=top_k, db_session=session
    )

    # Step 2: Fetch conversation history from PostgreSQL if available
    history_dicts: List[Dict[str, str]] = []
    conv_id = conversation_id or "ephemeral_session"
    if session is not None:
        try:
            conv_repo = ConversationRepository(session)
            conv = await conv_repo.get_or_create_conversation(conversation_id)
            conv_id = conv.id
            messages = await conv_repo.get_messages(conv.id, limit=6)
            for m in messages:
                history_dicts.append({"role": m.role, "content": m.content})
            # Log user message
            await conv_repo.add_message(conv_id, role="user", content=user_message)
        except Exception as e:
            logger.warning(f"Failed to load conversation history from PostgreSQL: {e}")

    # Step 3: Emit citations header event
    citations_data = [c.model_dump() for c in citations]
    header_payload = {
        "event": "citations",
        "conversation_id": conv_id,
        "sources": citations_data,
        "model": groq_model,
        "state": "THINKING",
    }
    yield f"data: {json.dumps(header_payload)}\n\n"

    # Step 4: Fallback if Groq unavailable
    if not client:
        if close_session_on_exit and session is not None:
            await session.close()
        fallback_msg = "I'm having trouble connecting to my AI thinking space (Groq API). Please verify your GROQ_API_KEY."
        yield f"data: {json.dumps({'token': fallback_msg, 'state': 'ERROR'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Step 5: Build grounded messages
    messages = build_grounded_messages(
        user_query=user_message,
        context=context,
        conversation_history=history_dicts,
    )

    full_reply = ""
    try:
        stream = await client.chat.completions.create(
            model=groq_model,
            messages=messages,
            temperature=0.4,  # Lower temperature for grounded factual precision
            max_tokens=1024,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                token = delta.content or ""
                if token:
                    full_reply += token
                    payload = {
                        "token": token,
                        "state": "THINKING",
                        "model": groq_model,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

        # Step 6: Persist assistant turn & audit in PostgreSQL
        if session is not None and full_reply:
            try:
                conv_repo = ConversationRepository(session)
                audit_repo = AuditRepository(session)
                await conv_repo.add_message(
                    conv_id, role="assistant", content=full_reply, sources=citations_data
                )
                await audit_repo.log_event(
                    event_type="rag_generation",
                    details={
                        "query": user_message,
                        "sources_count": len(citations_data),
                        "model": groq_model,
                    },
                )
                await session.commit()
            except Exception as e:
                logger.warning(f"Failed to persist assistant message to PostgreSQL: {e}")

        yield f"data: {json.dumps({'state': 'COMPLETE', 'conversation_id': conv_id})}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Groq RAG streaming error: {type(e).__name__} - {e}")
        err_msg = "An error occurred during enterprise response generation. Please try again."
        yield f"data: {json.dumps({'token': err_msg, 'state': 'ERROR'})}\n\n"
        yield "data: [DONE]\n\n"
    finally:
        if close_session_on_exit and session is not None:
            await session.close()
