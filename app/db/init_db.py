"""
app/db/init_db.py
─────────────────
Database initialisation:
  1. Create all SQLModel tables (idempotent — safe to call multiple times).
  2. Seed positions from MY_POSITIONS env var on first run.
  3. Seed a default alert rule if none exist.

Called from `app/lifespan.py` during FastAPI startup.
Also usable as a standalone script:  python -m app.db.init_db
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
from app.db.session import AsyncSessionLocal, engine
from app.models import AlertRule, Position, PositionCreate

logger = logging.getLogger(__name__)
settings = get_settings()


async def create_tables() -> None:
    """Create all tables defined by SQLModel metadata."""
    # Import all models so SQLModel registers their metadata
    import app.models  # noqa: F401

    from sqlmodel import SQLModel as _SQLModel

    async with engine.begin() as conn:
        await conn.run_sync(_SQLModel.metadata.create_all)

    logger.info("✅ Database tables created (or already exist)")


async def seed_positions(session: AsyncSession) -> None:
    """
    Load positions from MY_POSITIONS env var.
    Only inserts tickers that don't already exist in the DB.
    """
    positions = settings.positions
    if not positions:
        logger.info("No MY_POSITIONS configured — skipping position seed")
        return

    for pos in positions:
        # Check if ticker already exists
        stmt = select(Position).where(Position.ticker == pos.ticker)
        existing = (await session.exec(stmt)).first()

        if existing:
            logger.debug("Position %s already in DB — skipping", pos.ticker)
            continue

        new_pos = Position(
            ticker=pos.ticker,
            name=pos.name,
            quantity=pos.quantity,
        )
        session.add(new_pos)
        logger.info("  + Seeded position: %s (%s)", pos.ticker, pos.name)

    await session.commit()
    logger.info("✅ Positions seeded from MY_POSITIONS")


async def seed_default_alert_rule(session: AsyncSession) -> None:
    """Create a default catch-all alert rule if no rules exist."""
    stmt = select(AlertRule).limit(1)
    existing = (await session.exec(stmt)).first()

    if existing:
        logger.debug("Alert rules already exist — skipping default seed")
        return

    default_rule = AlertRule(
        score_threshold=settings.alert_score_threshold,
        channels="websocket"
        + (",telegram" if settings.tg_enabled else "")
        + (",discord" if settings.discord_enabled else ""),
        description="Default rule (seeded from .env on first startup)",
    )
    session.add(default_rule)
    await session.commit()
    logger.info("✅ Default alert rule created (threshold=%d)", settings.alert_score_threshold)


async def init_db() -> None:
    """Full initialization sequence — call this on app startup."""
    logger.info("Initializing database...")

    await create_tables()

    async with AsyncSessionLocal() as session:
        await seed_positions(session)
        await seed_default_alert_rule(session)

    logger.info("Database initialization complete ✨")


# ── Standalone entrypoint ────────────────────────────────────────────

if __name__ == "__main__":
    import rich.logging
    logging.basicConfig(
        level=logging.INFO,
        handlers=[rich.logging.RichHandler()],
    )
    asyncio.run(init_db())
