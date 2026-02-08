# Deployment Guide

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Vercel     │     │   Fly.io     │     │  ClickHouse  │
│  (Frontend)  │────▶│  (API/Proxy) │────▶│   Cloud      │
│  Next.js     │     │  FastAPI     │     │ (Time-Series)│
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┼──────┐
                    │      │      │
               ┌────▼───┐ ┌▼────┐ ┌▼────────┐
               │Supabase│ │Redis│ │LLM APIs  │
               │(Postgres)│(Upstash)│(OpenAI...)│
               └────────┘ └─────┘ └──────────┘
```

## 1. Backend Deployment (Fly.io)

### Prerequisites
- Fly.io account (`flyctl auth login`)
- Docker installed locally

### Steps

```bash
# 1. Create Fly.io app
flyctl apps create tokenmeter-api

# 2. Set secrets
flyctl secrets set \
  DATABASE_URL="postgresql://..." \
  REDIS_URL="redis://..." \
  CLICKHOUSE_HOST="..." \
  CLICKHOUSE_PASSWORD="..." \
  OPENAI_API_KEY="sk-..." \
  ANTHROPIC_API_KEY="sk-ant-..." \
  GOOGLE_API_KEY="AIza..." \
  STRIPE_SECRET_KEY="sk_live_..." \
  CLERK_SECRET_KEY="sk_live_..."

# 3. Deploy
flyctl deploy --config infra/fly.toml

# 4. Verify
curl https://tokenmeter-api.fly.dev/health
```

### Scaling

```bash
# Scale to 2 machines in 2 regions
flyctl scale count 2
flyctl regions add lhr  # London
```

## 2. Frontend Deployment (Vercel)

```bash
cd frontend

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_API_URL=https://tokenmeter-api.fly.dev
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...

vercel --prod
```

## 3. Database Setup

### PostgreSQL (Supabase)

1. Create project at [supabase.com](https://supabase.com)
2. Run the schema: `database/postgresql/schema.sql`
3. Run seed data: `database/seed.sql`
4. Copy the connection string to `DATABASE_URL`

### ClickHouse Cloud

1. Create service at [clickhouse.cloud](https://clickhouse.cloud)
2. Run the schema: `database/clickhouse/schema.sql`
3. Note host, user, password for env vars

### Redis (Upstash)

1. Create database at [upstash.com](https://upstash.com)
2. Copy the Redis URL to `REDIS_URL`

## 4. Domain & SSL

Fly.io provides automatic TLS. For custom domain:

```bash
flyctl certs create api.tokenmeter.dev
# Add CNAME: api.tokenmeter.dev → tokenmeter-api.fly.dev
```

## 5. Monitoring

- **Fly.io Dashboard**: CPU, memory, network metrics
- **ClickHouse**: Query the `request_logs` table for application metrics
- **Health endpoint**: `GET /health` returns system status
