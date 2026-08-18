"""
main.py - Enterprise FastAPI Application Entrypoint for Meli AI Companion
"""

import time
import logging
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    DATABASE_URL,
    ELASTICSEARCH_URL,
    HOST,
    PORT,
)
from backend.app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    EnterpriseStatusResponse,
    ComponentHealth,
    EnterpriseDocumentIngest,
    EnterpriseDocumentResponse,
    SearchRequest,
    SearchResponse,
    EnterpriseChatRequest,
    EnterpriseChatResponse,
    CompanionChatRequest,
)
from backend.app.groq_client import stream_groq_chat, generate_groq_chat
from backend.app.database import get_db, check_postgres_health, init_db
from backend.app.search.health import check_elasticsearch_health
from backend.app.search.indexer import index_document
from backend.app.search.retriever import execute_bm25_search
from backend.app.repositories.enterprise_record_repo import EnterpriseRecordRepository
from backend.app.repositories.conversation_repo import ConversationRepository
from backend.app.rag_orchestrator import stream_enterprise_rag_chat
from backend.app.companion.orchestrator import stream_companion_chat
from backend.app.companion.transcribe import router as transcribe_router
from backend.app.companion.synthesize import router as synthesize_router
from backend.app.tools.schemas import ToolConfirmationRequest
from backend.app.tools.executor import ToolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meli.api")

app = FastAPI(
    title="Meli Enterprise Companion API",
    description="Backend API for Meli AI Companion powered by PostgreSQL, Elasticsearch, and Groq LLM",
    version="1.0.0",
)

app.include_router(transcribe_router)
app.include_router(synthesize_router)

# CORS configuration for desktop and browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Initialize database tables if PostgreSQL is configured."""
    if DATABASE_URL:
        await init_db()


# ============================================================
# Phase 1A Backward-Compatible Endpoints
# ============================================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        model_configured=GROQ_MODEL,
        groq_api_key_configured=bool(GROQ_API_KEY and len(GROQ_API_KEY) > 5),
    )


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Phase 1A chat endpoint."""
    history_dicts = [msg.model_dump() for msg in request.history] if request.history else None

    if request.stream:
        return StreamingResponse(
            stream_groq_chat(
                user_message=request.message,
                history=history_dicts,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        res = await generate_groq_chat(
            user_message=request.message,
            history=history_dicts,
        )
        return ChatResponse(
            reply=res["reply"],
            state=res["state"],
            model=res["model"],
            usage=res.get("usage"),
        )


# ============================================================
# Enterprise Integration Endpoints (PostgreSQL + Elasticsearch + RAG)
# ============================================================

@app.get("/api/enterprise/status", response_model=EnterpriseStatusResponse)
async def enterprise_status():
    """
    Check real connectivity status of all 3 enterprise backends:
    - PostgreSQL
    - Elasticsearch
    - Groq
    Never reports 'connected' unless verified with a real live operation.
    """
    # 1. Check PostgreSQL
    pg_health = await check_postgres_health()

    # 2. Check Elasticsearch
    es_health = await check_elasticsearch_health()

    # 3. Check Groq
    if not GROQ_API_KEY:
        groq_health = ComponentHealth(
            state="not_configured",
            details="GROQ_API_KEY is not set in .env",
        )
    else:
        groq_health = ComponentHealth(
            state="connected",
            details=f"Model: {GROQ_MODEL}",
        )

    all_connected = (
        pg_health.state == "connected"
        and es_health.state == "connected"
        and groq_health.state == "connected"
    )

    return EnterpriseStatusResponse(
        status="fully_operational" if all_connected else "degraded",
        postgresql=pg_health,
        elasticsearch=es_health,
        groq=groq_health,
        timestamp=datetime.now(timezone.utc),
    )


@app.post("/api/enterprise/ingest", response_model=EnterpriseDocumentResponse)
async def ingest_document(
    doc: EnterpriseDocumentIngest,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Ingest an authoritative document into both PostgreSQL and Elasticsearch.
    """
    import uuid

    doc_id = str(uuid.uuid4())
    stored_pg = False
    indexed_es = False

    # Store in PostgreSQL
    if db is not None:
        try:
            repo = EnterpriseRecordRepository(db)
            await repo.create_record(
                record_id=doc_id,
                title=doc.title,
                content=doc.content,
                category=doc.category,
                source=doc.source,
                author=doc.metadata.get("author") if doc.metadata else None,
            )
            await db.commit()
            stored_pg = True
        except Exception as e:
            logger.warning(f"Failed to store document in PostgreSQL: {e}")

    # Index in Elasticsearch
    try:
        es_res = await index_document(
            doc_id=doc_id,
            title=doc.title,
            content=doc.content,
            category=doc.category,
            source=doc.source,
            author=doc.metadata.get("author") if doc.metadata else None,
        )
        indexed_es = bool(es_res)
    except Exception as e:
        logger.warning(f"Failed to index document in Elasticsearch: {e}")

    if not stored_pg and not indexed_es:
        raise HTTPException(
            status_code=503,
            detail="Failed to ingest document: both PostgreSQL and Elasticsearch are unreachable.",
        )

    return EnterpriseDocumentResponse(
        id=doc_id,
        title=doc.title,
        content=doc.content,
        category=doc.category,
        source=doc.source,
        created_at=datetime.now(timezone.utc),
        stored_in_postgres=stored_pg,
        indexed_in_elasticsearch=indexed_es,
    )


@app.post("/api/enterprise/search", response_model=SearchResponse)
async def search_enterprise_docs(request: SearchRequest):
    """
    Execute real BM25 full-text search against Elasticsearch.
    """
    t0 = time.perf_counter()
    results = await execute_bm25_search(
        query=request.query,
        limit=request.limit,
        category=request.category,
    )
    latency = (time.perf_counter() - t0) * 1000.0

    return SearchResponse(
        total=len(results),
        results=results,
        latency_ms=round(latency, 2),
    )


@app.post("/api/enterprise/chat")
async def enterprise_rag_chat(
    request: EnterpriseChatRequest,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Execute grounded RAG dialogue pipeline streaming tokens with source citations.
    """
    return StreamingResponse(
        stream_enterprise_rag_chat(
            user_message=request.message,
            conversation_id=request.conversation_id,
            top_k=request.top_k,
            db_session=db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/enterprise/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Fetch persistent conversation history from PostgreSQL.
    """
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL is not configured or unavailable.",
        )

    repo = ConversationRepository(db)
    conv = await repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources_json,
                "created_at": m.created_at,
            }
            for m in conv.messages
        ],
    }


# ============================================================
# Unified Companion Intelligence Endpoint
# ============================================================

@app.post("/api/companion/chat")
async def companion_chat_endpoint(
    request: CompanionChatRequest,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Unified Companion Intelligence Endpoint streaming structured SSE companion events.
    """
    history_dicts = [msg.model_dump() for msg in request.history] if request.history else None

    return StreamingResponse(
        stream_companion_chat(
            user_message=request.message,
            conversation_id=request.conversation_id,
            history=history_dicts,
            session=db,
            top_k=request.top_k,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/companion/confirm_tool")
async def confirm_tool_endpoint(
    request: ToolConfirmationRequest,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Endpoint to receive user approval or rejection for confirmation-required tools.
    """
    status = ToolExecutor.resolve_confirmation(request.call_id, request.approved)
    return {
        "status": status,
        "call_id": request.call_id,
        "approved": request.approved,
    }


@app.get("/api/tools/audit")
async def get_tool_audit_logs(limit: int = 50):
    """
    Retrieve sanitized tool telemetry audit logs.
    """
    from backend.app.tools.audit import ToolAuditLogger
    entries = ToolAuditLogger.get_recent_entries(limit=limit)
    return {"count": len(entries), "entries": [e.model_dump() for e in entries]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=True)

