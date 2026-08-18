"""
conversation_repo.py - PostgreSQL repository for Conversations and Messages
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.models import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_conversation(self, conversation_id: Optional[str] = None, title: str = "Enterprise Dialogue") -> Conversation:
        if conversation_id:
            stmt = select(Conversation).where(Conversation.id == conversation_id).options(selectinload(Conversation.messages))
            result = await self.session.execute(stmt)
            conv = result.scalar_one_or_none()
            if conv:
                return conv

        conv_id = conversation_id or str(uuid.uuid4())
        conv = Conversation(id=conv_id, title=title)
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources_json=sources,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get_messages(self, conversation_id: str, limit: int = 20) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
