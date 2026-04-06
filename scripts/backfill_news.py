#!/usr/bin/env python3
"""Manually trigger all collectors once and ingest results."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import AsyncSessionLocal, create_db_and_tables
from app.services.news_service import NewsService
from app.collectors.jin10 import Jin10Collector
from app.collectors.cls import CLSCollector
from app.collectors.reuters import ReutersCollector

async def main():
    await create_db_and_tables()
    collectors = [Jin10Collector(), CLSCollector(), ReutersCollector()]
    async with AsyncSessionLocal() as session:
        svc = NewsService(session)
        total = 0
        for c in collectors:
            print(f"Fetching {c.source}...")
            items = await c.fetch()
            for raw in items:
                result = await svc.ingest(raw)
                if result:
                    total += 1
    print(f"Ingested {total} new items.")

asyncio.run(main())
