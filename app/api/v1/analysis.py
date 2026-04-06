from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.db.crud import news as news_crud
from app.db.crud import analysis as analysis_crud
from app.services.analysis_service import AnalysisService
from app.models.analysis import AnalysisResultRead

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{news_id}", response_model=AnalysisResultRead)
async def get_analysis(news_id: int, session: AsyncSession = Depends(get_session)):
    result = await analysis_crud.get_by_news_id(session, news_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.post("/{news_id}/trigger", response_model=AnalysisResultRead)
async def trigger_analysis(news_id: int, session: AsyncSession = Depends(get_session)):
    news = await news_crud.get_by_guid(session, str(news_id))
    if not news:
        from sqlmodel import select
        from app.models.news import NewsItem
        q = select(NewsItem).where(NewsItem.id == news_id)
        r = await session.execute(q)
        news = r.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="News item not found")
    svc = AnalysisService(session)
    result = await svc.analyze_news(news)
    if not result:
        raise HTTPException(status_code=500, detail="Analysis failed — check Ollama connection")
    return result


@router.get("", response_model=list[AnalysisResultRead])
async def list_recent_analyses(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    return await analysis_crud.get_recent(session, limit=limit)
