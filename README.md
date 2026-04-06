<div align="center">

<!-- Logo / Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:203a43,100:2c5364&height=200&section=header&text=⚡%20finai-flash&fontSize=64&fontColor=ffffff&fontAlignY=38&desc=Your%20Local%20AI%20Bloomberg%20Terminal%20-%20Zero%20Cost%2C%20Zero%20Leaks&descAlignY=62&descSize=18" alt="finai-flash banner" width="100%"/>

<!-- Badges -->
[![GitHub Stars](https://img.shields.io/github/stars/yourname/finai-flash?style=for-the-badge&logo=github&color=FFD700&labelColor=0d1117)](https://github.com/yourname/finai-flash/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge&logo=opensourceinitiative&logoColor=white&labelColor=0d1117)](LICENSE)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourname/finai-flash?style=for-the-badge&logo=docker&color=2496ED&labelColor=0d1117)](https://hub.docker.com/r/yourname/finai-flash)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-ff6b35?style=for-the-badge&logo=llama&logoColor=white&labelColor=0d1117)](https://ollama.com)
[![Self Hosted](https://img.shields.io/badge/Self--Hosted-100%25-9333ea?style=for-the-badge&logo=homeassistant&logoColor=white&labelColor=0d1117)](https://github.com/yourname/finai-flash)

<br/>

> **🇨🇳 中文** | [🇬🇧 English](#english-version)

---

### 本地运行的「AI信息分析终端」——完全自托管，零 API 费用，零隐私泄露，秒级市场分析。
### *Your self-hosted AI financial terminal — real-time news, local LLM analysis, zero cloud dependency.*

</div>

---

## 🇨🇳 中文文档

### 这是什么？

**finai-flash** 是一个完全运行在你本地机器上的 AI 金融快讯分析系统。  
它像金十数据一样实时抓取财经快讯，但多了一层 **Ollama 本地大模型**的智能加持——  
每条新闻秒级生成：市场影响评分 · 利多/利空判断 · 交易建议 · 针对你持仓的个性化解读。

> 没有 OpenAI 账单。没有数据上传到云端。没有月费。你的仓位信息永远只在你的硬盘里。

---

### ✨ 功能亮点

| 功能 | 说明 |
|------|------|
| 📡 **实时快讯抓取** | 金十数据、财联社、Bloomberg RSS、Reuters 等多源聚合，延迟 <5s |
| 🧠 **本地 AI 分析** | Ollama 驱动（Qwen2.5 / DeepSeek / Llama3 任选），无需联网推理 |
| 📊 **市场影响评分** | 每条快讯自动打分 1-10，标注利多🟢 / 利空🔴 / 中性⚪ |
| 💼 **持仓个性化分析** | 输入你的持仓后，AI 直接告诉你"这条新闻对你的 A 股 / 港股 / 美股有什么影响" |
| 💡 **交易建议生成** | 简短、直接的操作参考（买入 / 观望 / 减仓），附置信度说明 |
| 🔔 **多渠道推送** | Telegram Bot / Discord Webhook 实时通知重要快讯 |
| 🐳 **一键 Docker 部署** | 三分钟跑起来，无需任何 Python 环境配置 |
| 🌓 **深色终端 UI** | 交易员友好的 Web 界面，仿彭博终端风格 |

---

### 🎬 30 秒演示

<div align="center">

```
┌─────────────────────────────────────────────────────────────────┐
│  [GIF 占位]  finai-flash 实时演示                                  │
│                                                                   │
│  → 金十快讯滚动推送                                                │
│  → Ollama 本地模型秒级响应                                         │
│  → 自动生成利多/利空 + 交易建议                                     │
│  → Telegram 推送到手机                                             │
│                                                                   │
│  📌 TODO: 替换为真实 demo.gif（建议用 asciinema 录制）              │
└─────────────────────────────────────────────────────────────────┘
```

*上图：终端启动 → 快讯接收 → AI 分析 → Telegram 推送，全流程约 8 秒*

</div>

---

### ⚡ 一键安装

> **前置要求：** 安装 [Docker](https://docs.docker.com/get-docker/) + [Ollama](https://ollama.com/download) 并拉取你喜欢的模型

```bash
# 1. 拉取并运行（默认使用 qwen2.5:7b）
docker run -d \
  --name finai-flash \
  -p 8888:8888 \
  -e OLLAMA_HOST=host.docker.internal:11434 \
  -e MODEL=qwen2.5:7b \
  -e TG_BOT_TOKEN=your_token \        # 可选
  -e TG_CHAT_ID=your_chat_id \        # 可选
  -v finai-data:/app/data \
  yourname/finai-flash:latest

# 2. 打开 Web UI
open http://localhost:8888
```

或者使用 **docker-compose**（推荐）：

```bash
git clone https://github.com/yourname/finai-flash.git
cd finai-flash
cp .env.example .env   # 编辑你的配置
docker compose up -d
```

---

### 🚀 快速开始

#### 第一步：配置你的持仓（可选但强烈推荐）

编辑 `.env` 文件中的持仓配置，或在 Web UI 中直接录入：

```env
# .env 示例
MY_POSITIONS=600519.SH:茅台:100股, 00700.HK:腾讯:200股, TSLA:特斯拉:50股
ALERT_SCORE_THRESHOLD=7        # 市场影响分 ≥7 才推送通知
MODEL=qwen2.5:7b               # 或 deepseek-r1:8b / llama3.1:8b
```

#### 第二步：选择你的本地模型

```bash
# 推荐组合（按性能/速度平衡排序）
ollama pull qwen2.5:7b          # 🥇 中文最优，速度快，推荐首选
ollama pull deepseek-r1:8b      # 🥈 推理强，适合复杂宏观分析
ollama pull llama3.1:8b         # 🥉 英文财经新闻分析佳
```

#### 第三步：启动并享用

```bash
docker compose up -d
# 访问 http://localhost:8888
```

你会看到：

```
⚡ finai-flash v0.1.0 已启动
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 数据源: 金十数据 ✓  财联社 ✓  Reuters ✓
🧠 模型:   qwen2.5:7b @ localhost:11434
💼 持仓:   茅台 · 腾讯 · 特斯拉 (3只)
🔔 推送:   Telegram ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
等待快讯...
```

---

### 🛠️ 技术栈

```
┌─────────────────────────────────────────────────┐
│                  finai-flash                     │
│                                                  │
│  数据层          处理层           输出层           │
│  ┌──────────┐   ┌────────────┐  ┌────────────┐  │
│  │ RSS Feed │──▶│  FastAPI   │─▶│  Web UI    │  │
│  │ 金十/财联社│   │  Parser    │  │ (Vue3+Vite)│  │
│  └──────────┘   └─────┬──────┘  └────────────┘  │
│                        │                          │
│                   ┌────▼──────┐  ┌────────────┐  │
│                   │  Ollama   │  │  Telegram  │  │
│                   │ Local LLM │  │  Discord   │  │
│                   └───────────┘  └────────────┘  │
│                                                  │
│  存储: SQLite + Redis(可选)  容器: Docker Compose  │
└─────────────────────────────────────────────────┘
```

| 组件 | 技术 |
|------|------|
| 后端 API | Python 3.11 · FastAPI · APScheduler |
| AI 推理 | Ollama · LangChain · 支持所有 GGUF 模型 |
| 数据抓取 | feedparser · httpx · BeautifulSoup4 |
| 前端 | Vue 3 · Vite · TailwindCSS（终端风格） |
| 推送 | python-telegram-bot · discord-webhook |
| 存储 | SQLite（默认）· Redis（高频场景） |
| 部署 | Docker · Docker Compose |

---

### 🗺️ 未来规划

- [ ] 🌐 **更多数据源** — 东方财富、雪球、Investing.com、X/Twitter 财经账号
- [ ] 📈 **K线图联动** — 快讯时间轴叠加在 TradingView 图表上
- [ ] 🤖 **Agent 模式** — 自动追踪某只股票的所有相关新闻，生成持续报告
- [ ] 📱 **移动端 PWA** — 手机直接访问，无需 App
- [ ] 🔗 **券商 API 对接** — 富途 / Interactive Brokers 直接下单（实验性）
- [ ] 🧪 **回测模块** — 验证历史快讯对价格的实际影响
- [ ] 🌍 **多语言** — 日本語 · 한국어 · Español 界面支持
- [ ] ☁️ **可选云模式** — 低配机器可接入 Groq / OpenRouter 免费额度

---

### 🤝 贡献指南

```bash
# Fork 项目后
git clone https://github.com/yourname/finai-flash.git
cd finai-flash
pip install -e ".[dev]"
pre-commit install

# 提交前请确保通过测试
pytest tests/ -v
```

欢迎任何形式的贡献：新数据源适配、模型提示词优化、UI 改进、文档翻译。  
请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

---

### ⚠️ 免责声明

本项目仅供学习和研究用途。所有 AI 生成的分析内容**不构成投资建议**。  
市场有风险，交易需谨慎。作者不对任何投资损失负责。

---

### ⭐ Star 历史

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=CanXINlol/finai-flash&type=Date)](https://star-history.com/#CanXINlol/finai-flash&Date)

*如果这个项目对你有帮助，请给个 Star ⭐ 支持一下！*

</div>

---

<br/><br/>

---

<div align="center" id="english-version">

## 🇬🇧 English Documentation

</div>

### What is finai-flash?

**finai-flash** is a fully self-hosted AI financial news terminal that runs entirely on your local machine.  
Think of it as a personal Bloomberg terminal powered by a local LLM — it aggregates real-time financial news and generates instant AI analysis for every headline:

- 📊 **Market Impact Score** (1–10)
- 🟢🔴 **Bullish / Bearish classification**
- 💡 **Trading suggestions** with confidence rating
- 💼 **Personalized analysis** based on your portfolio

> No OpenAI bill. No data leaving your machine. No subscription. Your positions stay on your disk.

---

### ✨ Feature Highlights

| Feature | Description |
|---------|-------------|
| 📡 **Real-time News Feed** | Aggregates Jin10, CLS, Bloomberg RSS, Reuters & more. Latency <5s |
| 🧠 **Local AI Inference** | Powered by Ollama (Qwen2.5 / DeepSeek / Llama3 — your choice) |
| 📊 **Impact Scoring** | Auto-scores each headline 1–10, tags Bullish🟢 / Bearish🔴 / Neutral⚪ |
| 💼 **Portfolio-Aware Analysis** | AI tells you exactly how each headline affects *your* specific positions |
| 💡 **Trade Signal Generation** | Clear, concise action suggestions (Buy / Hold / Reduce) with reasoning |
| 🔔 **Multi-Channel Alerts** | Telegram Bot + Discord Webhook for high-impact news push |
| 🐳 **One-Command Deploy** | Up and running in 3 minutes, no Python setup required |
| 🌓 **Terminal-Style UI** | Bloomberg-inspired dark web interface built for traders |

---

### 🎬 30-Second Demo

<div align="center">

```
┌─────────────────────────────────────────────────────────────────┐
│  [GIF PLACEHOLDER]  finai-flash Live Demo                        │
│                                                                   │
│  → Real-time headline streaming                                   │
│  → Ollama local model responds in <3s                             │
│  → Auto-generates Bullish/Bearish + trade suggestion              │
│  → Pushes to Telegram instantly                                   │
│                                                                   │
│  📌 TODO: Replace with real demo.gif (record with asciinema)     │
└─────────────────────────────────────────────────────────────────┘
```

*Full flow: terminal boot → headline ingestion → AI analysis → Telegram push, ~8 seconds total*

</div>

---

### ⚡ One-Command Install

> **Prerequisites:** [Docker](https://docs.docker.com/get-docker/) + [Ollama](https://ollama.com/download) with your preferred model pulled

```bash
# Pull and run (defaults to qwen2.5:7b)
docker run -d \
  --name finai-flash \
  -p 8888:8888 \
  -e OLLAMA_HOST=host.docker.internal:11434 \
  -e MODEL=qwen2.5:7b \
  -e TG_BOT_TOKEN=your_token \        # optional
  -e TG_CHAT_ID=your_chat_id \        # optional
  -v finai-data:/app/data \
  yourname/finai-flash:latest

# Open Web UI
open http://localhost:8888
```

Or use **docker-compose** (recommended):

```bash
git clone https://github.com/yourname/finai-flash.git
cd finai-flash
cp .env.example .env   # Edit your config
docker compose up -d
```

---

### 🚀 Quick Start

#### Step 1: Configure your portfolio (optional but highly recommended)

```env
# .env example
MY_POSITIONS=AAPL:Apple:50shares, NVDA:Nvidia:30shares, BTC:Bitcoin:0.5
ALERT_SCORE_THRESHOLD=7        # Only push alerts for impact score ≥ 7
MODEL=qwen2.5:7b               # or deepseek-r1:8b / llama3.1:8b
```

#### Step 2: Choose your local model

```bash
ollama pull qwen2.5:7b          # 🥇 Best for Chinese news, fast response
ollama pull deepseek-r1:8b      # 🥈 Superior reasoning for macro analysis
ollama pull llama3.1:8b         # 🥉 Best for English-language financial news
```

#### Step 3: Launch

```bash
docker compose up -d
# Visit http://localhost:8888
```

---

### 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11 · FastAPI · APScheduler |
| AI Inference | Ollama · LangChain · Any GGUF model |
| News Scraping | feedparser · httpx · BeautifulSoup4 |
| Frontend | Vue 3 · Vite · TailwindCSS (terminal theme) |
| Notifications | python-telegram-bot · discord-webhook |
| Storage | SQLite (default) · Redis (high-frequency mode) |
| Deployment | Docker · Docker Compose |

---

### 🗺️ Roadmap

- [ ] 🌐 **More Sources** — Eastmoney, Xueqiu, Investing.com, Financial Twitter
- [ ] 📈 **TradingView Integration** — Overlay news events on price charts
- [ ] 🤖 **Agent Mode** — Auto-track all news for a specific ticker, generate continuous reports
- [ ] 📱 **Mobile PWA** — Access from phone without an app
- [ ] 🔗 **Broker API** — Futu / Interactive Brokers direct order execution (experimental)
- [ ] 🧪 **Backtesting Module** — Validate historical news impact on price action
- [ ] 🌍 **i18n** — Japanese · Korean · Spanish UI support
- [ ] ☁️ **Optional Cloud Mode** — Route to Groq / OpenRouter free tier for low-spec machines

---

### 📄 License

MIT © 2025 [CanXINlol](https://github.com/yourname)

---

<div align="center">

**Built by traders, for traders. 🚀**

*If finai-flash saves you from making a bad trade, consider giving it a ⭐*

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:2c5364,50:203a43,100:0f2027&height=100&section=footer" width="100%"/>

</div>
