from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings

settings = get_settings()
scheduler = AsyncIOScheduler()


def start_scheduler(news_service):
    if scheduler.running:
        return

    from app.collectors.cctv_finance import CCTVFinanceCollector
    from app.collectors.cls import CLSCollector
    from app.collectors.jin10 import Jin10Collector

    collectors = [Jin10Collector(), CLSCollector(), CCTVFinanceCollector()]

    async def collect_all():
        for collector in collectors:
            try:
                items = await collector.fetch()
                for raw in items:
                    await news_service.ingest(raw)
            except Exception as exc:
                print(f"[Scheduler] collector error from {collector.__class__.__name__}: {exc}")

    scheduler.add_job(
        collect_all,
        trigger="interval",
        seconds=settings.collect_interval_seconds,
        id="collect_all",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    print(f"[Scheduler] started, interval={settings.collect_interval_seconds}s")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
