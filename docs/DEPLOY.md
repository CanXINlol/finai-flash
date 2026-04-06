# FinAI-Flash Deployment

## Quick Start

1. Copy the example environment file.

```bash
cp .env.example .env
```

2. Optionally edit `.env`.

Recommended defaults for a 16 GB RAM machine:

```env
MODEL=qwen2.5:7b
COLLECT_INTERVAL_SECONDS=300
AUTO_ANALYZE_FLASH=true
```

3. Start the full stack.

```bash
docker compose up -d
```

4. Open the app.

```text
http://localhost:8888
```

## What Starts

- `finai-flash`: FastAPI backend plus built frontend assets
- `ollama`: local model runtime
- `ollama-init`: one-shot model pull for `${MODEL}`
- `rsshub`: local RSS source aggregator
- `rsshub-redis`: Redis cache for RSSHub

## First Boot Notes

- The first run can take several minutes because `ollama-init` downloads the model.
- `qwen2.5:7b` is the safest default for 16 GB RAM machines.
- `qwen2.5:14b` may work on stronger machines, but will be slower.
- `qwen2.5:32b` is not recommended for 16 GB RAM hosts.

## Useful Commands

Show running services:

```bash
docker compose ps
```

Watch backend logs:

```bash
docker compose logs -f finai-flash
```

Watch model pull progress:

```bash
docker compose logs -f ollama-init
```

Watch RSSHub logs:

```bash
docker compose logs -f rsshub
```

Stop everything:

```bash
docker compose down
```

Stop everything and remove volumes:

```bash
docker compose down -v
```

## Health Checks

Backend:

```bash
curl http://localhost:8888/health
```

Latest flash items:

```bash
curl http://localhost:8888/api/flash
```

## GPU Notes

The compose file includes a commented NVIDIA reservation block under the `ollama` service.
Uncomment it only if your Docker host already has GPU container runtime support configured.
