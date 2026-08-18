"""
test_enterprise_database.py - Unit and Integration Tests for PostgreSQL Layer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.models import Conversation, Message, EnterpriseRecord, AuditEvent, Base
from backend.app.database import check_postgres_health, get_engine, init_db, normalize_postgres_url
from backend.app.repositories.conversation_repo import ConversationRepository
from backend.app.repositories.enterprise_record_repo import EnterpriseRecordRepository
from backend.app.repositories.audit_repo import AuditRepository


def test_normalize_postgres_url():
    """Verify URL normalization handles SSL parameters, schemes, and connect_args correctly."""
    # 1. Neon/Cloud PostgreSQL URL with sslmode=require
    raw_neon = "postgresql://user:secret@ep-cool-snowflake.us-east-2.aws.neon.tech/neondb?sslmode=require"
    cleaned, connect_args = normalize_postgres_url(raw_neon)
    assert cleaned.startswith("postgresql+asyncpg://")
    assert "sslmode" not in cleaned
    assert connect_args.get("ssl") == "require"
    assert connect_args.get("timeout") == 15

    # 2. Supabase/standard postgres:// URL with sslmode=verify-full and channel_binding=disable (both should be stripped)
    raw_supa = "postgres://postgres:pass@db.project.supabase.co:5432/postgres?sslmode=verify-full&channel_binding=disable&command_timeout=20"
    cleaned, connect_args = normalize_postgres_url(raw_supa)
    assert cleaned.startswith("postgresql+asyncpg://")
    assert "sslmode" not in cleaned
    assert "channel_binding" not in cleaned
    assert "command_timeout=20" in cleaned
    assert connect_args.get("ssl") == "require"

    # 3. Localhost database without SSL
    raw_local = "postgresql://postgres:pass@127.0.0.1:5432/localdb"
    cleaned, connect_args = normalize_postgres_url(raw_local)
    assert cleaned == "postgresql+asyncpg://postgres:pass@127.0.0.1:5432/localdb"
    assert "ssl" not in connect_args

    # 4. Empty URL
    cleaned, connect_args = normalize_postgres_url("")
    assert cleaned == ""
    assert connect_args == {}


def test_model_definitions():
    """Verify SQLAlchemy 2.x declarative models have correct table and column attributes."""
    assert Conversation.__tablename__ == "conversations"
    assert Message.__tablename__ == "messages"
    assert EnterpriseRecord.__tablename__ == "enterprise_records"
    assert AuditEvent.__tablename__ == "audit_events"

    # Test column names
    conv_cols = [c.name for c in Conversation.__table__.columns]
    assert "id" in conv_cols
    assert "title" in conv_cols
    assert "created_at" in conv_cols
    assert "metadata_json" in conv_cols

    msg_cols = [c.name for c in Message.__table__.columns]
    assert "id" in msg_cols
    assert "conversation_id" in msg_cols
    assert "role" in msg_cols
    assert "content" in msg_cols
    assert "sources_json" in msg_cols


@pytest.mark.asyncio
async def test_postgres_health_not_configured():
    """When DATABASE_URL is empty, status must report 'not_configured'."""
    with patch("backend.app.database.DATABASE_URL", ""):
        health = await check_postgres_health()
        assert health.state == "not_configured"
        assert "not set" in health.details


@pytest.mark.asyncio
async def test_postgres_health_unavailable_on_connection_error():
    """When connection fails, health check must report 'unavailable' with error details."""
    with patch("backend.app.database.DATABASE_URL", "postgresql+asyncpg://invalid:pass@127.0.0.1:5432/nonexistent"):
        with patch("backend.app.database.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = ConnectionRefusedError("Connection refused to 127.0.0.1:5432")
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn
            mock_get_engine.return_value = mock_engine

            health = await check_postgres_health()
            assert health.state == "unavailable"
            assert "Connection refused" in (health.details or "")


@pytest.mark.asyncio
async def test_postgres_health_connected_on_select_1():
    """When 'SELECT 1' returns 1, health check reports 'connected'."""
    with patch("backend.app.database.DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db"):
        with patch("backend.app.database.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_conn = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_conn.execute.return_value = mock_result
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn
            mock_get_engine.return_value = mock_engine

            health = await check_postgres_health()
            assert health.state == "connected"
            assert health.latency_ms is not None
            assert health.latency_ms >= 0


@pytest.mark.asyncio
async def test_conversation_repository_crud():
    """Test ConversationRepository operations with an AsyncSession mock."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    repo = ConversationRepository(mock_session)

    # 1. Create conversation
    conv = await repo.get_or_create_conversation(conversation_id="conv-123", title="Test Chat")
    assert conv.id == "conv-123"
    assert conv.title == "Test Chat"
    mock_session.add.assert_called()
    mock_session.flush.assert_called()

    # 2. Add message
    msg = await repo.add_message(
        conversation_id="conv-123",
        role="user",
        content="Hello Meli!",
        sources=[{"title": "Doc A"}],
    )
    assert msg.conversation_id == "conv-123"
    assert msg.role == "user"
    assert msg.content == "Hello Meli!"


@pytest.mark.asyncio
async def test_enterprise_record_repository():
    """Test EnterpriseRecordRepository record creation."""
    mock_session = AsyncMock()
    repo = EnterpriseRecordRepository(mock_session)

    rec = await repo.create_record(
        title="Incident SLA Policy",
        content="Sev-1 response time < 15 minutes",
        category="operations",
        source="handbook",
        author="SRE Team",
    )
    assert rec.title == "Incident SLA Policy"
    assert rec.category == "operations"
    assert rec.source == "handbook"
    mock_session.add.assert_called()
