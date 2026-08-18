"""
backend.app.companion package initialization
"""

from backend.app.companion.events import (
    CompanionEvent,
    CompanionEventType,
    create_thinking_event,
    create_memory_event,
    create_stream_event,
    create_completed_event,
    create_error_event,
)
from backend.app.companion.persona import (
    PersonaConfig,
    DEFAULT_PERSONA,
    build_persona_prompt,
)
from backend.app.companion.memory import (
    MemoryDecision,
    MemoryItem,
    should_remember,
    store_episodic_memory,
    retrieve_memories,
)
from backend.app.companion.orchestrator import (
    assemble_companion_context,
    stream_companion_chat,
)

__all__ = [
    "CompanionEvent",
    "CompanionEventType",
    "create_thinking_event",
    "create_memory_event",
    "create_stream_event",
    "create_completed_event",
    "create_error_event",
    "PersonaConfig",
    "DEFAULT_PERSONA",
    "build_persona_prompt",
    "MemoryDecision",
    "MemoryItem",
    "should_remember",
    "store_episodic_memory",
    "retrieve_memories",
    "assemble_companion_context",
    "stream_companion_chat",
]
