from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import get_settings

settings = get_settings()


def _ensure_sqlite_directory(database_url: str) -> None:
    parsed_url = make_url(database_url)
    if not parsed_url.drivername.startswith("sqlite") or not parsed_url.database:
        return
    if parsed_url.database == ":memory:":
        return

    db_path = Path(parsed_url.database)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory(settings.database_url)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.run_sync(_apply_sqlite_migrations)


def _apply_sqlite_migrations(sync_conn) -> None:
    inspector = inspect(sync_conn)
    if not inspector.has_table("app_settings"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("app_settings")}
    wanted_columns = {
        "model": "TEXT",
        "auto_analyze_flash": "BOOLEAN",
        "live_market_quotes": "BOOLEAN",
        "collect_interval_seconds": "INTEGER",
        "updated_at": "DATETIME",
    }

    for column_name, column_type in wanted_columns.items():
        if column_name not in existing_columns:
            sync_conn.execute(
                text(f"ALTER TABLE app_settings ADD COLUMN {column_name} {column_type}")
            )
