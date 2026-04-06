from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_news_service
from app.models.news import FlashItemRead
from app.services.news_service import NewsService

router = APIRouter(tags=["flash"])


@router.get("/flash", response_model=list[FlashItemRead])
async def get_flash(
    limit: int = Query(10, ge=1, le=100),
    svc: NewsService = Depends(get_news_service),
):
    return await svc.get_latest_flash(limit=limit)
