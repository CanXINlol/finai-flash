from __future__ import annotations
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.analysis import AnalysisResult


async def create(session: AsyncSession, result: AnalysisResult) -> AnalysisResult:
    session.add(result)
    await session.commit()
    await session.refresh(result)
    return result


async def get_by_news_id(session: AsyncSession, news_id: int) -> Optional[AnalysisResult]:
    q = select(AnalysisResult).where(AnalysisResult.news_id == news_id)
    result = await session.execute(q)
    return result.scalar_one_or_none()


async def get_recent(session: AsyncSession, limit: int = 20) -> list[AnalysisResult]:
    q = select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()
