from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings

settings = get_settings()
scheduler = AsyncIOScheduler()
_news_service = None
_current_interval = settings.collect_interval_seconds


async def _collect_all():
    if _news_service is None:
        return

    from app.collectors.cctv_finance import CCTVFinanceCollector
    from app.collectors.cls import CLSCollector
    from app.collectors.jin10 import Jin10Collector

    collectors = [Jin10Collector(), CLSCollector(), CCTVFinanceCollector()]
    for collector in collectors:
        try:
            items = await collector.fetch()
            for raw in items:
                await _news_service.ingest(raw)
        except Exception as exc:
            print(f"[Scheduler] collector error from {collector.__class__.__name__}: {exc}")


def start_scheduler(news_service, interval_seconds: int | None = None):
    global _news_service, _current_interval
    _news_service = news_service
    _current_interval = interval_seconds or settings.collect_interval_seconds

    scheduler.add_job(
        _collect_all,
        trigger="interval",
        seconds=_current_interval,
        id="collect_all",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    if not scheduler.running:
        scheduler.start()
    print(f"[Scheduler] started, interval={_current_interval}s")


def reschedule_collection(interval_seconds: int) -> None:
    global _current_interval
    _current_interval = interval_seconds
    if scheduler.get_job("collect_all") is None:
        return
    scheduler.reschedule_job("collect_all", trigger="interval", seconds=interval_seconds)
    print(f"[Scheduler] rescheduled, interval={interval_seconds}s")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
