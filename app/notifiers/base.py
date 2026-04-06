from __future__ import annotations
from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    name: str = "base"

    @abstractmethod
    async def send(self, title: str, body: str, score: int, sentiment: str) -> bool:
        """Send a notification. Returns True on success."""
        ...
