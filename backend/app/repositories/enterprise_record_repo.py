"""
enterprise_record_repo.py - PostgreSQL repository for Authoritative Knowledge Records
"""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models import EnterpriseRecord


class EnterpriseRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_record(
        self,
        title: str,
        content: str,
        category: str = "general",
        source: str = "internal_kb",
        author: Optional[str] = None,
        record_id: Optional[str] = None,
    ) -> EnterpriseRecord:
        rec = EnterpriseRecord(
            id=record_id or str(uuid.uuid4()),
            title=title,
            content=content,
            category=category,
            source=source,
            author=author,
        )
        self.session.add(rec)
        await self.session.flush()
        return rec

    async def get_by_id(self, record_id: str) -> Optional[EnterpriseRecord]:
        stmt = select(EnterpriseRecord).where(EnterpriseRecord.id == record_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_matching_records(self, query: str, limit: int = 5) -> List[EnterpriseRecord]:
        """Search PostgreSQL structured records using ILIKE pattern matching."""
        pattern = f"%{query}%"
        stmt = (
            select(EnterpriseRecord)
            .where(
                (EnterpriseRecord.title.ilike(pattern))
                | (EnterpriseRecord.content.ilike(pattern))
                | (EnterpriseRecord.category.ilike(pattern))
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
