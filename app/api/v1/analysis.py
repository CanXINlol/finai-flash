from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import analysis as analysis_crud
from app.db.crud import news as news_crud
from app.db.session import get_session
from app.dependencies import get_flash_analysis_service
from app.models.analysis import AnalysisResultRead
from app.models.flash_analysis import FlashAnalysis, FlashAnalyzeRequest
from app.services.analysis_service import AnalysisService
from app.services.flash_analysis_service import FlashAnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/flash", response_model=FlashAnalysis)
async def analyze_flash(
    data: FlashAnalyzeRequest,
    svc: FlashAnalysisService = Depends(get_flash_analysis_service),
):
    try:
        svc.ensure_ready()
        return await svc.analyze(data)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Flash analysis failed: {exc}") from exc


@router.post("/flash/stream")
async def stream_flash_analysis(
    data: FlashAnalyzeRequest,
    svc: FlashAnalysisService = Depends(get_flash_analysis_service),
):
    try:
        svc.ensure_ready()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    async def streamer():
        try:
            async for chunk in svc.stream_json(data):
                yield chunk.encode("utf-8")
        except RuntimeError as exc:
            yield json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")

    return StreamingResponse(streamer(), media_type="application/json; charset=utf-8")


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

        query = select(NewsItem).where(NewsItem.id == news_id)
        result = await session.execute(query)
        news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="News item not found")

    svc = AnalysisService(session)
    result = await svc.analyze_news(news)
    if not result:
        raise HTTPException(status_code=500, detail="Analysis failed; check Ollama connection")
    return result


@router.get("", response_model=list[AnalysisResultRead])
async def list_recent_analyses(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    return await analysis_crud.get_recent(session, limit=limit)
