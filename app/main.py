from __future__ import annotations

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.ai.ollama_client import get_ollama_client
from app.api import flash
from app.api.v1 import alerts, analysis, news, portfolio
from app.config import get_settings
from app.lifespan import lifespan
from app.responses import UTF8JSONResponse
from app.websocket.manager import flash_manager, manager

settings = get_settings()

app = FastAPI(
    title="finai-flash",
    version="0.1.0",
    description="Local AI financial news terminal",
    lifespan=lifespan,
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(news.router, prefix=API_PREFIX)
app.include_router(analysis.router, prefix=API_PREFIX)
app.include_router(portfolio.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(flash.router, prefix="/api")


@app.get("/health", tags=["system"])
async def health():
    ollama_ok = await get_ollama_client().health_check()
    return {
        "status": "ok",
        "ollama": "connected" if ollama_ok else "unreachable",
        "model": settings.model,
        "ws_clients": manager.active_count,
        "flash_ws_clients": flash_manager.active_count,
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)


@app.websocket("/ws/flash")
async def flash_websocket_endpoint(ws: WebSocket):
    await flash_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await flash_manager.disconnect(ws)


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):

        @app.get("/", include_in_schema=False)
        async def serve_index():
            return FileResponse(index_path)

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            return FileResponse(index_path)
