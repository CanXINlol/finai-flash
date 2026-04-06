import sqlite3
import asyncio
import json
import feedparser
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ==========================================
# Configuration / 配置
# ==========================================
DB_FILE = "flash_news.db"

# RSS 源配置 (默认使用 RSSHub 路由格式)
# RSS Sources configuration (Defaults are based on RSSHub routes)
RSS_SOURCES = [
    {"name": "金十数据", "url": "https://rsshub.app/jin10"},
    {"name": "财联社", "url": "https://rsshub.app/cailianshe/telegraph"},
    {"name": "央视财经", "url": "https://rsshub.app/cctv/category/jingji"}
]

# ==========================================
# Database Initialization / 数据库初始化
# ==========================================
def init_db():
    """Create table with UNIQUE constraints for deduplication"""
    """创建数据表，利用 UNIQUE 约束实现 title + pub_date 去重"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flash_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            link TEXT,
            pub_date TEXT,
            UNIQUE(title, pub_date)
        )
    ''')
    conn.commit()
    conn.close()

# ==========================================
# WebSocket Manager / WebSocket 管理器
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Broadcast new items to all active clients"""
        """向所有连接的客户端广播新消息"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# ==========================================
# RSS Fetching Logic / RSS 抓取逻辑
# ==========================================
def fetch_rss_sync() -> list:
    """
    Sync function to fetch and store RSS feeds. 
    Returns newly inserted items.
    同步函数：抓取 RSS 并存入 SQLite，返回本次新增的快讯。
    """
    new_items = []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                pub_date = entry.get("published", "")

                # Check if item exists to accurately push only NEW items
                # 检查是否存在，以便精准提取新快讯用于 WebSocket 推送
                cursor.execute("SELECT id FROM flash_news WHERE title=? AND pub_date=?", (title, pub_date))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO flash_news (source, title, link, pub_date)
                        VALUES (?, ?, ?, ?)
                    ''', (source["name"], title, link, pub_date))
                    
                    new_items.append({
                        "id": cursor.lastrowid,
                        "source": source["name"],
                        "title": title,
                        "link": link,
                        "pub_date": pub_date
                    })
        except Exception as e:
            print(f"Error fetching {source['name']}: {e}")

    conn.commit()
    conn.close()
    return new_items

async def scheduled_fetch_job():
    """
    Run sync fetch in executor to prevent blocking the event loop.
    在线程池中执行同步抓取，防止阻塞 FastAPI 的主事件循环。
    """
    loop = asyncio.get_event_loop()
    new_items = await loop.run_in_executor(None, fetch_rss_sync)
    
    if new_items:
        # Push new items via WebSocket / 通过 WebSocket 推送新快讯
        print(f"Fetched {len(new_items)} new items. Broadcasting...")
        await manager.broadcast(json.dumps(new_items, ensure_ascii=False))

# ==========================================
# FastAPI Application & Lifespan / 应用与生命周期
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Init Database / 初始化数据库
    init_db()
    
    # 2. Setup Scheduler / 配置并启动定时器
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_fetch_job, 'interval', minutes=5)
    scheduler.start()
    
    # Trigger an initial fetch right on startup / 启动时立即抓取一次
    asyncio.create_task(scheduled_fetch_job())
    
    yield
    
    # 3. Shutdown Scheduler / 关闭定时器
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Setup CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# API Endpoints / API 路由
# ==========================================
@app.get("/api/flash")
def get_latest_flash():
    """
    Retrieve the latest 10 flash news items from the database.
    获取数据库中最新的 10 条快讯。
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Fetch top 10 descending by ID / 按 ID 倒序取 10 条
    cursor.execute("SELECT id, source, title, link, pub_date FROM flash_news ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()

    result = [
        {"id": r[0], "source": r[1], "title": r[2], "link": r[3], "pub_date": r[4]}
        for r in rows
    ]
    return {"status": "success", "data": result}

@app.websocket("/ws/flash")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time news push.
    提供给前端建立长连接，实时接收新快讯推送的 WebSocket 端点。
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages if any
            # 保持连接，接收客户端可能发送的心跳或消息
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)