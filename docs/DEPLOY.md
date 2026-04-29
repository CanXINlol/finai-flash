# FinAI-Flash Deployment Guide

FinAI-Flash is designed as a self-hosted financial flash news terminal: low-cost RSS aggregation, local LLM analysis, SQLite persistence, and a browser dashboard.

## Recommended Defaults

These defaults are tuned for a practical MVP on a Windows machine with about 16 GB RAM and an 8 GB GPU. If Docker cannot access the GPU, Ollama will run on CPU, so stability matters more than maximum model size.

| Setting | Recommended | Why |
| --- | --- | --- |
| `MODEL` | `qwen2.5:7b` | Good Chinese JSON reliability, fits local machines better than 14B/32B. |
| `COLLECT_INTERVAL_SECONDS` | `300` | Matches the product goal of near-real-time RSS without overloading SQLite or Ollama. |
| `AUTO_ANALYZE_FLASH` | `true` | Keeps the dashboard useful automatically. |
| `AUTO_ANALYSIS_MAX_PENDING` | `3` | Prevents slow local inference from creating an infinite backlog. |
| `LIVE_MARKET_QUOTES` | `true` | Lets analysis identify related market assets. |
| `MARKET_QUOTE_EXACT_PRICES` | `false` | Keep false unless you connect a trusted quote provider; avoids AI using mismatched free-source prices. |
| `MARKET_QUOTE_TIMEOUT_SECONDS` | `4` | Avoids Yahoo/yfinance latency blocking AI analysis. |
| `OLLAMA_NUM_CTX` | `2048` | Enough context for flash analysis, much lighter than 4096/8192. |
| `OLLAMA_NUM_PREDICT` | `768` | Enough room for strict JSON while reducing CPU inference time. |
| `OLLAMA_TEMPERATURE` | `0.05` | More deterministic JSON output. |
| `OLLAMA_TIMEOUT` | `180` | Allows CPU inference to finish without hanging forever. |

## Quick Start

```powershell
cd C:\Users\CanXIN\Desktop\finai-flash\finai-flash
copy .env.example .env
docker compose up -d
```

Open:

```text
http://127.0.0.1:8888
```

Check health:

```powershell
Invoke-RestMethod http://127.0.0.1:8888/health
```

## First Boot

The first run may take several minutes because Docker needs to pull images and Ollama may need to pull the selected model.

If `ollama-init` fails because DNS cannot reach the Ollama registry, the app can still start when the model already exists in the `ollama-models` volume. The compose file intentionally does not block forever on model pull failure.

## Common Commands

Show services:

```powershell
docker compose ps
```

Watch backend logs:

```powershell
docker logs --tail 120 finai-flash
```

Watch Ollama logs:

```powershell
docker logs --tail 120 finai-ollama
```

Restart only the backend:

```powershell
docker compose up -d --build finai-flash
```

Stop services without deleting data:

```powershell
docker compose down
```

## Safe Cleanup

Safe cleanup removes generated cache and Docker build cache. It does not delete SQLite data or Ollama models.

```powershell
.\scripts\cleanup-dev.ps1
```

Equivalent manual commands:

```powershell
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item .\.pytest_cache -Recurse -Force -ErrorAction SilentlyContinue
docker builder prune -f
```

Avoid this unless you intentionally want to remove containers/images:

```powershell
docker system prune -a -f
```

Avoid this unless you intentionally want to delete all app data and downloaded Ollama models:

```powershell
docker compose down -v
```

## Manual AI Analysis Test

Use the dashboard `Manual Analyzer`, or call the API directly:

```powershell
$body = @{
  text = "OPEC+据称正在讨论延长自愿减产期限，国际油价盘中快速走高。"
  positions = @("原油多单", "黄金")
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8888/api/v1/analysis/flash" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

## GPU Notes

The compose file uses `gpus: all` for Ollama. This only helps if Docker Desktop can access your GPU runtime. If Ollama logs show `total_vram="0 B"` or `inference compute ... cpu`, it is running on CPU.

For CPU-only Docker inference, keep `qwen2.5:7b`, `OLLAMA_NUM_CTX=2048`, and `OLLAMA_NUM_PREDICT=768`.

For a faster setup, run Ollama directly on Windows and point the backend to the host Ollama service:

```env
OLLAMA_HOST=http://host.docker.internal:11434
```

Then disable or remove the compose `ollama` dependency if you want to fully externalize Ollama later.
