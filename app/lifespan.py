from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import create_db_and_tables
from app.collectors.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ─────────────────────────────────────
    await create_db_and_tables()

    # Lazy import to avoid circular deps at module load
    from app.db.session import AsyncSessionLocal
    from app.services.news_service import NewsService

    async def _get_news_service():
        async with AsyncSessionLocal() as session:
            return NewsService(session)

    # Scheduler needs a factory, not a single service instance
    from app.collectors.scheduler import start_scheduler
    from app.db.session import AsyncSessionLocal as ASL
    from app.services.news_service import NewsService as NS

    class _NewsServiceProxy:
        async def ingest(self, raw):
            async with ASL() as session:
                svc = NS(session)
                return await svc.ingest(raw)

    start_scheduler(_NewsServiceProxy())
    print("[Lifespan] DB ready, scheduler running")

    yield  # ── application runs ──────────────────────

    # ── Shutdown ────────────────────────────────────
    stop_scheduler()
    print("[Lifespan] shutdown complete")
