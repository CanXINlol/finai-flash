from __future__ import annotations
from app.config import get_settings
from app.notifiers.base import BaseNotifier

settings = get_settings()

_notifiers: list[BaseNotifier] = []


def get_notifiers() -> list[BaseNotifier]:
    global _notifiers
    if _notifiers:
        return _notifiers
    if settings.telegram_enabled():
        from app.notifiers.telegram import TelegramNotifier
        _notifiers.append(TelegramNotifier())
    if settings.discord_enabled():
        from app.notifiers.discord import DiscordNotifier
        _notifiers.append(DiscordNotifier())
    return _notifiers


async def dispatch(title: str, body: str, score: int, sentiment: str) -> dict[str, bool]:
    results = {}
    for n in get_notifiers():
        results[n.name] = await n.send(title=title, body=body, score=score, sentiment=sentiment)
    return results
