from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.lifespan import lifespan
from app.api.v1 import news, analysis, portfolio, alerts
from app.websocket.manager import manager
from app.ai.ollama_client import get_ollama_client
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="finai-flash",
    version="0.1.0",
    description="Local AI financial news terminal",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST API routes ──────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(news.router,      prefix=API_PREFIX)
app.include_router(analysis.router,  prefix=API_PREFIX)
app.include_router(portfolio.router, prefix=API_PREFIX)
app.include_router(alerts.router,    prefix=API_PREFIX)


# ── Health check ─────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health():
    ollama_ok = await get_ollama_client().health_check()
    return {
        "status": "ok",
        "ollama": "connected" if ollama_ok else "unreachable",
        "model": settings.model,
        "ws_clients": manager.active_count,
    }


# ── WebSocket endpoint ───────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()   # keep-alive ping
    except WebSocketDisconnect:
        await manager.disconnect(ws)


# ── Serve Vue frontend (production) ──────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        index = os.path.join(STATIC_DIR, "index.html")
        return FileResponse(index)
