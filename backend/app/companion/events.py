"""
events.py - Typed Structured Companion Event Protocol for Meli AI Companion
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


CompanionEventType = Literal[
    "THINKING",
    "MEMORY_RETRIEVED",
    "TOOL_REQUESTED",
    "TOOL_CONFIRMATION_REQUIRED",
    "TOOL_STARTED",
    "TOOL_COMPLETED",
    "TOOL_FAILED",
    "RESPONSE_STREAM",
    "RESPONSE_COMPLETED",
    "ERROR",
]


class CompanionEvent(BaseModel):
    """Authoritative backend companion event schema."""
    type: CompanionEventType
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    token: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    visual_hint: Optional[str] = None
    source: Optional[str] = None

    def to_sse_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary formatted for SSE client."""
        return {
            "type": self.type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "token": self.token,
            "message": self.message,
            "metadata": self.metadata or {},
            "visual_hint": self.visual_hint,
            "source": self.source,
        }

    def to_sse_line(self) -> str:
        """Format as SSE event string."""
        import json
        return f"data: {json.dumps(self.to_sse_dict())}\n\n"


def create_thinking_event(message: str = "Thinking...", source: str = "orchestrator") -> CompanionEvent:
    return CompanionEvent(
        type="THINKING",
        message=message,
        visual_hint="focused",
        source=source,
    )


def create_memory_event(
    memories_count: int,
    summary: str,
    metadata: Optional[Dict[str, Any]] = None,
    source: str = "memory_layer",
) -> CompanionEvent:
    return CompanionEvent(
        type="MEMORY_RETRIEVED",
        message=summary,
        metadata={"count": memories_count, **(metadata or {})},
        visual_hint="curious",
        source=source,
    )


def create_tool_requested_event(
    tool_name: str,
    reason: Optional[str] = None,
    call_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    source: str = "tool_orchestrator",
) -> CompanionEvent:
    return CompanionEvent(
        type="TOOL_REQUESTED",
        message=f"Action requested: {tool_name}",
        metadata={"tool": tool_name, "reason": reason, "call_id": call_id, **(metadata or {})},
        visual_hint="focused",
        source=source,
    )


def create_tool_confirmation_required_event(
    tool_name: str,
    prompt: str,
    call_id: str,
    arguments: Optional[Dict[str, Any]] = None,
    source: str = "tool_policy",
) -> CompanionEvent:
    return CompanionEvent(
        type="TOOL_CONFIRMATION_REQUIRED",
        message=prompt,
        metadata={"tool": tool_name, "call_id": call_id, "arguments": arguments or {}},
        visual_hint="curious",
        source=source,
    )


def create_tool_started_event(
    tool_name: str,
    description: str,
    call_id: Optional[str] = None,
    source: str = "tool_executor",
) -> CompanionEvent:
    return CompanionEvent(
        type="TOOL_STARTED",
        message=description,
        metadata={"tool": tool_name, "call_id": call_id},
        visual_hint="working",
        source=source,
    )


def create_tool_completed_event(
    tool_name: str,
    summary: str,
    result_data: Optional[Any] = None,
    call_id: Optional[str] = None,
    duration_ms: float = 0.0,
    source: str = "tool_executor",
) -> CompanionEvent:
    return CompanionEvent(
        type="TOOL_COMPLETED",
        message=summary,
        metadata={
            "tool": tool_name,
            "call_id": call_id,
            "data": result_data,
            "duration_ms": duration_ms,
        },
        visual_hint="complete",
        source=source,
    )


def create_tool_failed_event(
    tool_name: str,
    error_message: str,
    call_id: Optional[str] = None,
    source: str = "tool_executor",
) -> CompanionEvent:
    return CompanionEvent(
        type="TOOL_FAILED",
        message=f"Tool failed: {error_message}",
        metadata={"tool": tool_name, "call_id": call_id, "error": error_message},
        visual_hint="error",
        source=source,
    )


def create_stream_event(token: str, source: str = "groq_llm") -> CompanionEvent:
    return CompanionEvent(
        type="RESPONSE_STREAM",
        token=token,
        source=source,
    )


def create_completed_event(
    full_content: str,
    metadata: Optional[Dict[str, Any]] = None,
    source: str = "orchestrator",
) -> CompanionEvent:
    return CompanionEvent(
        type="RESPONSE_COMPLETED",
        message="Response completed",
        metadata={"length": len(full_content), **(metadata or {})},
        visual_hint="happy",
        source=source,
    )


def create_error_event(
    error_message: str,
    metadata: Optional[Dict[str, Any]] = None,
    source: str = "orchestrator",
) -> CompanionEvent:
    return CompanionEvent(
        type="ERROR",
        message=error_message,
        metadata=metadata or {},
        visual_hint="nervous",
        source=source,
    )
