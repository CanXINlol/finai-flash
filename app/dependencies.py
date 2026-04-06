from __future__ import annotations
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.services.news_service import NewsService
from app.services.analysis_service import AnalysisService
from app.services.portfolio_service import PortfolioService
from app.services.alert_service import AlertService


async def get_news_service(session: AsyncSession = Depends(get_session)) -> NewsService:
    return NewsService(session)


async def get_analysis_service(session: AsyncSession = Depends(get_session)) -> AnalysisService:
    return AnalysisService(session)


async def get_portfolio_service(session: AsyncSession = Depends(get_session)) -> PortfolioService:
    return PortfolioService(session)


async def get_alert_service(session: AsyncSession = Depends(get_session)) -> AlertService:
    return AlertService(session)
