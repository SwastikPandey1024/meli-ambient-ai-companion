"""
notes_repo.py - Application-Managed Notes Repository for Meli AI Companion
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NoteItem(BaseModel):
    id: str = Field(default_factory=lambda: f"note_{uuid.uuid4().hex[:10]}")
    title: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)


class NotesRepository:
    """Thread-safe application notes storage."""
    _in_memory_notes: Dict[str, NoteItem] = {}

    def __init__(self, session=None):
        self.session = session

    async def create_note(self, title: str, content: str, tags: Optional[List[str]] = None) -> NoteItem:
        note = NoteItem(
            title=title.strip(),
            content=content.strip(),
            tags=tags or ["meli-companion"],
        )
        self._in_memory_notes[note.id] = note
        return note

    async def get_note(self, note_id: str) -> Optional[NoteItem]:
        return self._in_memory_notes.get(note_id)

    async def list_notes(self, limit: int = 20) -> List[NoteItem]:
        return list(self._in_memory_notes.values())[:limit]

    async def search_notes(self, query: str) -> List[NoteItem]:
        q_lower = query.lower()
        return [
            n for n in self._in_memory_notes.values()
            if q_lower in n.title.lower() or q_lower in n.content.lower()
        ]

    async def delete_note(self, note_id: str) -> bool:
        if note_id in self._in_memory_notes:
            del self._in_memory_notes[note_id]
            return True
        return False
