#!/usr/bin/env python3
"""Seed sample portfolio positions into the database."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import AsyncSessionLocal, create_db_and_tables
from app.models.portfolio import Position
from datetime import datetime

SAMPLE_POSITIONS = [
    {"ticker": "600519.SH", "name": "Kweichow Moutai",  "quantity": 100.0, "market": "A-share"},
    {"ticker": "00700.HK",  "name": "Tencent Holdings",  "quantity": 200.0, "market": "HK"},
    {"ticker": "NVDA",      "name": "NVIDIA",             "quantity": 50.0,  "market": "US"},
    {"ticker": "BTC",       "name": "Bitcoin",            "quantity": 0.5,   "market": "Crypto"},
]

async def main():
    await create_db_and_tables()
    async with AsyncSessionLocal() as session:
        for p in SAMPLE_POSITIONS:
            pos = Position(**p, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            session.add(pos)
        await session.commit()
    print(f"Seeded {len(SAMPLE_POSITIONS)} positions.")

asyncio.run(main())
