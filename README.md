# ShiftChange-Bot

Voice-structured shift handover system for hospitals. Built for fast demo with synthetic patient data.

## 30-second Quick Start

```bash
cp .env.example .env
make dev
# Open http://localhost:5173
```

## Stack

| Layer    | Tech                                   |
|----------|----------------------------------------|
| Backend  | Python 3.12 + FastAPI + uv             |
| Frontend | Vite + React 18 + TypeScript + Tailwind |
| Layout   | PWA-optimized, mobile-first            |
| Container| Docker Compose                         |

## Development Commands

```bash
make dev          # Start full stack via Docker (hot-reload enabled)
make test         # Run backend tests locally (requires uv)
make test-docker  # Run backend tests inside Docker
make demo         # Start detached + print URLs
```

## API

- `GET /api/health` — service liveness check
- `GET /docs` — Swagger UI (dev only)

## Project Structure

```
backend/          FastAPI app (app/), pytest tests (tests/)
frontend/         Vite + React SPA, proxies /api/* to backend
infra/            Reserved for IaC / deployment configs
docker-compose.yml
Makefile
```
