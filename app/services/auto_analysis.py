from __future__ import annotations

import asyncio

from app.db.crud import news as news_crud
from app.db.session import AsyncSessionLocal
from app.services.analysis_service import AnalysisService
from app.config import get_settings

settings = get_settings()

_pending_news_ids: set[int] = set()
_background_tasks: set[asyncio.Task] = set()
_analysis_semaphore = asyncio.Semaphore(1)


async def _run_analysis(news_id: int) -> None:
    try:
        async with _analysis_semaphore:
            async with AsyncSessionLocal() as session:
                item = await news_crud.get_by_id(session, news_id)
                if not item:
                    return
                service = AnalysisService(session)
                await service.analyze_news(item)
    except Exception as exc:
        print(f"[AutoAnalysis] error for news {news_id}: {exc}")
    finally:
        _pending_news_ids.discard(news_id)


def schedule_auto_analysis(news_id: int) -> bool:
    if news_id in _pending_news_ids:
        return False
    if len(_pending_news_ids) >= settings.auto_analysis_max_pending:
        print(
            f"[AutoAnalysis] skipped news {news_id}: "
            f"pending queue reached {settings.auto_analysis_max_pending}"
        )
        return False

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return False

    _pending_news_ids.add(news_id)
    task = loop.create_task(_run_analysis(news_id))
    _background_tasks.add(task)

    def _cleanup(done_task: asyncio.Task) -> None:
        _background_tasks.discard(done_task)
        try:
            done_task.result()
        except Exception as exc:
            print(f"[AutoAnalysis] background task error for news {news_id}: {exc}")

    task.add_done_callback(_cleanup)
    return True
