from __future__ import annotations
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import get_settings

settings = get_settings()
scheduler = AsyncIOScheduler()


def start_scheduler(news_service):
    """Register all collectors and start the APScheduler."""
    from app.collectors.jin10 import Jin10Collector
    from app.collectors.cls import CLSCollector
    from app.collectors.reuters import ReutersCollector

    collectors = [Jin10Collector(), CLSCollector(), ReutersCollector()]

    async def collect_all():
        for collector in collectors:
            try:
                items = await collector.fetch()
                for raw in items:
                    await news_service.ingest(raw)
            except Exception as e:
                print(f"[Scheduler] collector error: {e}")

    scheduler.add_job(
        collect_all,
        trigger="interval",
        seconds=settings.collect_interval_seconds,
        id="collect_all",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[Scheduler] started, interval={settings.collect_interval_seconds}s")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
