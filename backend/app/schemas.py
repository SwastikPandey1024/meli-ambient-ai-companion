"""
schemas.py - Pydantic Schemas for Meli Companion & Enterprise AI RAG
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ============================================================
# Basic Chat Schemas (Phase 1A Backward Compatible)
# ============================================================

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: Optional[List[Message]] = None
    stream: bool = True


class ChatResponse(BaseModel):
    reply: str
    state: str = "COMPLETE"
    model: str
    usage: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    model_configured: str
    groq_api_key_configured: bool


# ============================================================
# Enterprise Integration Schemas (PostgreSQL + Elasticsearch + RAG)
# ============================================================

ServiceConnectionState = Literal["connected", "unavailable", "not_configured"]


class ComponentHealth(BaseModel):
    state: ServiceConnectionState
    details: Optional[str] = None
    latency_ms: Optional[float] = None


class EnterpriseStatusResponse(BaseModel):
    status: str = "operational"
    postgresql: ComponentHealth
    elasticsearch: ComponentHealth
    groq: ComponentHealth
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Document Ingestion
class EnterpriseDocumentIngest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=5)
    category: str = Field(default="general", max_length=64)
    source: str = Field(default="internal_kb", max_length=128)
    metadata: Optional[Dict[str, Any]] = None


class EnterpriseDocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str
    source: str
    created_at: datetime
    stored_in_postgres: bool = False
    indexed_in_elasticsearch: bool = False


# Search Request & Results
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    category: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=50)


class SearchResultItem(BaseModel):
    id: str
    title: str
    content: str
    snippet: str
    category: str
    source: str
    score: float
    source_type: str = "elasticsearch"


class SearchResponse(BaseModel):
    total: int
    results: List[SearchResultItem]
    latency_ms: float


# Grounded RAG Chat
class CitationSource(BaseModel):
    id: str
    title: str
    source: str
    snippet: str
    source_type: Literal["elasticsearch", "postgresql"]


class EnterpriseChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    stream: bool = True
    top_k: int = Field(default=4, ge=1, le=10)


class EnterpriseChatResponse(BaseModel):
    reply: str
    conversation_id: str
    sources: List[CitationSource] = []
    state: str = "COMPLETE"
    model: str
    usage: Optional[Dict[str, Any]] = None


# ============================================================
# Unified Companion Intelligence Endpoint Schemas
# ============================================================

class CompanionChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    history: Optional[List[Message]] = None
    top_k: int = Field(default=3, ge=1, le=10)


# ============================================================
# Phase 1D Tool Confirmation Request
# ============================================================

from backend.app.tools.schemas import ToolConfirmationRequest


