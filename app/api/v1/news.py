from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.dependencies import get_news_service
from app.services.news_service import NewsService
from app.models.news import NewsItemList, NewsSource

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=NewsItemList)
async def list_news(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    source: Optional[NewsSource] = None,
    since_hours: int = Query(24, ge=1, le=168),
    svc: NewsService = Depends(get_news_service),
):
    items, total = await svc.get_recent(
        limit=limit, offset=offset, source=source, since_hours=since_hours
    )
    return NewsItemList(items=items, total=total)
