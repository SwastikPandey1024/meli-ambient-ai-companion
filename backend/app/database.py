"""
database.py - Canonical PostgreSQL Async Engine, Session Factory, and Health Check
"""

import time
import logging
from typing import AsyncGenerator, Optional, Dict, Any, Tuple
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import text
from backend.app.config import DATABASE_URL
from backend.app.models import Base
from backend.app.schemas import ComponentHealth

logger = logging.getLogger("meli.database")

_async_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

# Known libpq-specific query parameters incompatible with asyncpg keyword arguments
LIBPQ_ONLY_PARAMS = {
    "sslmode",
    "ssl",
    "channel_binding",
    "gssencmode",
    "target_session_attrs",
    "connect_timeout",
    "application_name",
    "keepalives",
    "keepalives_idle",
    "keepalives_interval",
    "keepalives_count",
    "tcp_user_timeout",
    "client_encoding",
}


def normalize_postgres_url(raw_url: str) -> Tuple[str, Dict[str, Any]]:
    """
    Canonical PostgreSQL connection normalization for SQLAlchemy 2.x + asyncpg.

    Handles:
    - Scheme normalization (postgres:// / postgresql:// -> postgresql+asyncpg://)
    - Strips unsupported libpq query parameters (sslmode, channel_binding, gssencmode, etc.) from URL string
    - Translates SSL requirements (sslmode=require/prefer/verify-ca/verify-full) into asyncpg connect_args={'ssl': 'require'}
    - Preserves local non-SSL PostgreSQL connections
    - Never logs credentials or secrets
    """
    if not raw_url or not raw_url.strip():
        return "", {}

    raw_url = raw_url.strip()
    parsed = urlsplit(raw_url)

    # 1. Normalize driver scheme
    scheme = parsed.scheme.lower()
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"
    elif scheme == "postgresql+psycopg2":
        scheme = "postgresql+asyncpg"
    elif not scheme.startswith("postgresql+"):
        scheme = "postgresql+asyncpg"

    # 2. Parse and filter query parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    cleaned_params = []
    connect_args: Dict[str, Any] = {"timeout": 15}

    ssl_required = False
    for k, v in query_params:
        k_lower = k.lower()
        v_lower = v.lower()

        if k_lower == "sslmode":
            if v_lower in ("require", "prefer", "verify-ca", "verify-full"):
                ssl_required = True
            continue
        elif k_lower == "ssl":
            if v_lower in ("true", "1", "require"):
                ssl_required = True
            elif v_lower in ("false", "0", "disable"):
                ssl_required = False
            continue
        elif k_lower == "connect_timeout":
            try:
                connect_args["timeout"] = int(v)
            except ValueError:
                pass
            continue
        elif k_lower in LIBPQ_ONLY_PARAMS:
            # Strip libpq-specific parameters not recognized by asyncpg.connect()
            continue

        cleaned_params.append((k, v))

    if ssl_required:
        connect_args["ssl"] = "require"

    new_query = urlencode(cleaned_params)
    cleaned_url = urlunsplit((scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

    return cleaned_url, connect_args


def get_engine() -> Optional[AsyncEngine]:
    """Get or create singleton async SQLAlchemy engine."""
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        return _async_engine

    if not DATABASE_URL:
        return None

    try:
        cleaned_url, connect_args = normalize_postgres_url(DATABASE_URL)
        if not cleaned_url:
            return None

        _async_engine = create_async_engine(
            cleaned_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        _async_session_factory = async_sessionmaker(
            bind=_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info("PostgreSQL async engine initialized successfully.")
        return _async_engine
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL engine: {e}")
        return None


def get_session_factory() -> Optional[async_sessionmaker[AsyncSession]]:
    """Return configured async session factory."""
    if _async_session_factory is None:
        get_engine()
    return _async_session_factory


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """FastAPI dependency yielding an async database session."""
    factory = get_session_factory()
    if factory is None:
        yield None
        return

    async with factory() as session:
        try:
            yield session
            if session.is_active:
                await session.commit()
        except Exception:
            try:
                await session.rollback()
            except Exception:
                pass
            raise


async def check_postgres_health() -> ComponentHealth:
    """
    Perform a real query against the PostgreSQL database.
    Never reports 'connected' unless 'SELECT 1' succeeds.
    """
    if not DATABASE_URL:
        return ComponentHealth(
            state="not_configured",
            details="DATABASE_URL environment variable is not set.",
        )

    engine = get_engine()
    if engine is None:
        return ComponentHealth(
            state="unavailable",
            details="Could not initialize PostgreSQL engine with configured DATABASE_URL.",
        )

    t0 = time.perf_counter()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            latency = (time.perf_counter() - t0) * 1000.0

            if val == 1:
                return ComponentHealth(
                    state="connected",
                    details="PostgreSQL query 'SELECT 1' executed successfully.",
                    latency_ms=round(latency, 2),
                )
            else:
                return ComponentHealth(
                    state="unavailable",
                    details=f"Unexpected query result: {val}",
                    latency_ms=round(latency, 2),
                )
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000.0
        logger.warning(f"PostgreSQL health check failed: {type(e).__name__} - {e}")
        return ComponentHealth(
            state="unavailable",
            details=f"Connection failed ({type(e).__name__}): {str(e)}",
            latency_ms=round(latency, 2),
        )


async def init_db(engine: Optional[AsyncEngine] = None):
    """Create all schema tables in PostgreSQL if connected."""
    eng = engine or get_engine()
    if eng is None:
        logger.warning("Skipping table creation: PostgreSQL engine not configured.")
        return False
    try:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL schema tables created/verified successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to create schema tables: {e}")
        return False
