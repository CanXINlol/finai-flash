from __future__ import annotations

import asyncio
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.append(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections = [connection for connection in self._connections if connection is not ws]

    async def broadcast(self, data: dict):
        payload = json.dumps(data, ensure_ascii=False, default=str)
        dead_connections = []
        for ws in list(self._connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead_connections.append(ws)
        for ws in dead_connections:
            await self.disconnect(ws)

    @property
    def active_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
flash_manager = ConnectionManager()
