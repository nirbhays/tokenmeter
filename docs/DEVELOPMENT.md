# Local Development Guide

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- Git

## Setup

### 1. Clone & Configure

```bash
git clone https://github.com/tokenmeter/tokenmeter
cd tokenmeter
cp .env.example .env
```

Edit `.env` with your API keys (at minimum, set `OPENAI_API_KEY`).

### 2. Start Infrastructure

```bash
cd backend
docker-compose up -d
```

This starts:
- **PostgreSQL** on port 5432 (auto-runs schema.sql)
- **Redis** on port 6379
- **ClickHouse** on ports 8123/9000 (auto-runs schema.sql)

### 3. Start Backend

```bash
# From project root
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

The API is now at http://localhost:8000. Check http://localhost:8000/docs for Swagger UI.

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard at http://localhost:3000.

### 5. Test the Proxy

```bash
# Using the development bypass key
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer tm_dev_key_for_local_testing_only" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1-nano",
    "messages": [{"role": "user", "content": "Say hello"}]
  }'
```

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes* | At least one provider key needed |
| `ANTHROPIC_API_KEY` | No | Enable Anthropic models |
| `GOOGLE_API_KEY` | No | Enable Google models |
| `DATABASE_URL` | No | Defaults to local Docker PostgreSQL |
| `REDIS_URL` | No | Defaults to local Docker Redis |

## Running Tests

```bash
# Backend tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=backend --cov-report=html

# Python SDK tests
cd sdks/python && pip install -e ".[dev]" && pytest tests/

# Node.js SDK tests
cd sdks/node && npm install && npm test
```

## Linting

```bash
# Python
pip install ruff
ruff check backend/
ruff format backend/

# Frontend
cd frontend && npm run lint
```

## Debugging

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health
- **Logs**: stdout with structured format
- **ClickHouse**: http://localhost:8123 (HTTP interface)

## Common Issues

**"No provider available for model"**: Set at least one provider API key in `.env`.

**"Redis connection refused"**: Run `docker-compose up -d redis`.

**Token counting slow on first request**: tiktoken downloads encoding data on first use; subsequent calls are cached.
