# CLAUDE.md — TokenMeter

## What This Project Does

TokenMeter is an LLM cost intelligence layer that works as a drop-in replacement for OpenAI, Anthropic, and Google AI SDK imports. By changing one import line, every LLM call in an application is automatically intercepted by a local or hosted proxy that: tracks token counts and costs per request with 8-decimal-place precision, classifies request complexity using 8 heuristic signals, routes each request to the cheapest model capable of handling it (up to 60% cost reduction), enforces per-team/per-feature budget limits with Slack and webhook alerts, and displays everything on a real-time dashboard. The proxy overhead is under 5ms and supports streaming. It is also available as a base-URL override for any OpenAI-compatible HTTP client in any language.

---

## Owner Context

**Owner:** Nirbhay Singh — Cloud & AI Architect
**Career goal:** $800K USD total compensation as a Staff+/Principal AI Infrastructure Architect.
TokenMeter is a **portfolio project** targeting roles at AI-native companies and cloud hyperscalers where cost efficiency of AI workloads is a first-class concern. It demonstrates production-grade observability engineering, multi-provider abstraction, smart routing algorithms, and a polished SaaS billing/auth stack.

**Related repos in the portfolio (same owner: nirbhays):**
| Repo | What it does |
|---|---|
| `shieldiac` | IaC security scanner — GitHub App, 100+ rules, 9 compliance frameworks |
| `infracents` | GitHub App: Terraform cost estimates on every PR |
| `agent-loom` | Multi-agent orchestration framework |
| `airlock` | API gateway with rate limiting and auth for AI services |
| `model-ledger` | Audit trail and lineage tracking for ML models |
| `tune-forge` | Fine-tuning pipeline manager |
| `data-mint` | Synthetic data generation for LLM training |

TokenMeter and airlock are closely related — airlock handles auth/rate-limiting at the gateway level while TokenMeter handles cost attribution and routing at the application level. model-ledger tracks model versioning; TokenMeter tracks model usage costs.

---

## Complete File Structure

```
tokenmeter/
├── .env.example                        # All environment variables with comments
├── .github/
│   └── workflows/
│       ├── ci.yml                      # Tests + lint on every PR
│       ├── deploy.yml                  # Deploy backend to Fly.io on push to main
│       ├── publish-sdk-python.yml      # Publish Python SDK to PyPI on tag
│       └── publish-sdk-node.yml        # Publish Node.js SDK to npm on tag
├── backend/                            # Python 3.11 / FastAPI proxy + API
│   ├── __init__.py
│   ├── main.py                         # FastAPI app factory, router registration, lifespan hooks
│   ├── config.py                       # Pydantic BaseSettings — all config from env vars
│   ├── Dockerfile                      # Multi-stage build for Fly.io deployment
│   ├── docker-compose.yml              # Local dev: PostgreSQL + Redis + ClickHouse
│   ├── requirements.txt                # Production dependencies
│   ├── requirements-dev.txt            # Dev/test: pytest, ruff, httpx test client, coverage
│   ├── api/                            # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── proxy.py                    # POST /v1/chat/completions — main proxy endpoint
│   │   ├── routing.py                  # GET/POST /routing — routing rules CRUD, test routing decision
│   │   ├── budgets.py                  # GET/POST /budgets — team and feature budget management
│   │   ├── dashboard.py                # GET /dashboard — cost stats, charts, per-model breakdown
│   │   ├── keys.py                     # GET/POST /keys — API key management for multi-tenant use
│   │   ├── billing.py                  # POST /billing/webhook — Stripe webhook handler
│   │   └── health.py                   # GET /health — liveness probe
│   ├── middleware/                     # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── auth.py                     # API key validation and Clerk JWT verification
│   │   ├── logging.py                  # Structured request logging (respects ZERO_LOGGING_MODE)
│   │   └── rate_limiter.py             # Redis-backed per-key rate limiting
│   ├── models/                         # Pydantic v2 data models
│   │   ├── __init__.py
│   │   ├── proxy.py                    # ProxyRequest, ProxyResponse (extends OpenAI schema + tm_* fields)
│   │   ├── usage.py                    # UsageRecord, TokenCount, CostBreakdown
│   │   ├── routing.py                  # RoutingDecision, RoutingMode, ComplexityScore
│   │   ├── budget.py                   # Budget, BudgetAlert, AlertThreshold
│   │   ├── provider.py                 # Provider, ModelConfig, PricingTier
│   │   └── billing.py                  # Subscription, Plan, BillingEvent
│   ├── providers/                      # Per-provider LLM client adapters
│   │   ├── __init__.py
│   │   ├── base.py                     # BaseProvider: abstract interface all providers implement
│   │   ├── openai.py                   # OpenAI adapter (GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, o3, o4-mini)
│   │   ├── anthropic.py                # Anthropic adapter (Claude Opus 4, Sonnet 4.5, Haiku 3.5)
│   │   ├── google.py                   # Google adapter (Gemini 2.5 Pro, Gemini 2.5 Flash)
│   │   └── pricing.py                  # Pricing registry: per-model input/output token costs (updated regularly)
│   ├── services/                       # Business logic
│   │   ├── __init__.py
│   │   ├── proxy_handler.py            # Core proxy flow: classify -> route -> forward -> track
│   │   ├── request_classifier.py       # 8-signal complexity classifier (see below)
│   │   ├── routing_engine.py           # Model selection given complexity + routing mode
│   │   ├── cost_calculator.py          # Token-to-dollar calculation using pricing.py rates
│   │   ├── usage_tracker.py            # Write usage records to ClickHouse + PostgreSQL
│   │   ├── budget_monitor.py           # Check budgets, trigger alerts at 50%/80%/100% thresholds
│   │   ├── alert_service.py            # Send Slack webhooks, email alerts, generic webhooks
│   │   ├── analytics_service.py        # Aggregate usage data for dashboard queries
│   │   ├── cache_service.py            # Redis cache for routing decisions and model pricing
│   │   ├── provider_registry.py        # Manages available providers, health checks, failover
│   │   └── billing_service.py          # Stripe customer and subscription management
│   └── utils/                          # Shared utilities
│       ├── __init__.py
│       ├── token_counter.py            # tiktoken-based local token counting (used for pre-request estimates)
│       ├── streaming.py                # SSE/streaming response passthrough with cost tracking
│       └── security.py                 # API key hashing, HMAC utilities
├── sdks/                               # Client SDKs (published separately)
│   ├── python/                         # PyPI package: tokenmeter
│   │   ├── setup.py
│   │   ├── README.md
│   │   ├── tokenmeter/
│   │   │   ├── __init__.py             # Exposes OpenAI, Anthropic as drop-in replacements
│   │   │   ├── client.py               # Thin wrapper that points OpenAI/Anthropic clients at the proxy
│   │   │   └── types.py                # Extended response types with tm_cost_usd, tm_latency_ms, etc.
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_client.py
│   └── node/                           # npm package: tokenmeter
│       ├── package.json
│       ├── tsconfig.json
│       ├── README.md
│       └── src/
│           ├── index.ts                # Re-exports OpenAI as default, wraps with cost tracking
│           ├── client.ts               # Node.js proxy client implementation
│           └── types.ts                # TypeScript types extending OpenAI types
├── frontend/                           # Next.js 14 cost dashboard
│   └── src/
│       ├── app/                        # App Router pages
│       └── components/                 # React components (Recharts for cost graphs)
├── database/
│   ├── postgresql/
│   │   ├── schema.sql                  # Tables: api_keys, teams, features, budgets, subscriptions
│   │   └── migrations/
│   │       └── 001_initial.sql
│   ├── clickhouse/
│   │   └── schema.sql                  # usage_events table (materialized views for fast aggregation)
│   └── seed.sql                        # Sample teams, features, budgets for local dev
├── tests/                              # pytest test suite (backend only)
│   ├── __init__.py
│   ├── conftest.py                     # Fixtures: test client, mock providers, sample requests
│   ├── test_proxy_handler.py           # End-to-end proxy flow tests (providers mocked)
│   ├── test_request_classifier.py      # Complexity classification for various prompt types
│   ├── test_routing_engine.py          # Model selection logic for all 3 routing modes
│   ├── test_cost_calculator.py         # Token-to-dollar calculation accuracy
│   ├── test_token_counter.py           # tiktoken counting accuracy across models
│   ├── test_budget_monitor.py          # Budget threshold enforcement and alert triggering
│   ├── test_provider_openai.py         # OpenAI adapter: request formatting, response parsing
│   └── test_provider_anthropic.py      # Anthropic adapter: message format conversion
├── CHANGELOG.md
├── Makefile                            # Developer commands
├── pyproject.toml                      # Ruff, pytest, coverage configuration
├── LICENSE
└── README.md
```

---

## Environment Variables

Copy `.env.example` to `.env`. No prefix is used (unlike shieldiac). Key variables:

| Variable | Required | Description |
|---|:---:|---|
| `DATABASE_URL` | Yes | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `CLICKHOUSE_HOST` | Yes | ClickHouse host (default: `localhost`) |
| `CLICKHOUSE_DATABASE` | Yes | ClickHouse database name (default: `tokenmeter`) |
| `REDIS_URL` | Yes | Redis URL for cache and rate limiting |
| `OPENAI_API_KEY` | Yes* | OpenAI API key (at least one provider key required) |
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key |
| `GOOGLE_API_KEY` | Yes* | Google AI API key |
| `CLERK_SECRET_KEY` | Yes (prod) | Clerk for dashboard auth |
| `STRIPE_SECRET_KEY` | Yes (prod) | Stripe billing |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for budget alerts |
| `ROUTING_DEFAULT_MODE` | No | `cost-optimized` (default), `latency-optimized`, or `quality-optimized` |
| `ZERO_LOGGING_MODE` | No | `true` to disable storing request/response bodies |
| `CACHE_ENABLED` | No | `true` (default) — cache routing decisions and pricing |

---

## How to Develop Locally

```bash
# 1. Clone the repo
git clone https://github.com/nirbhays/tokenmeter.git
cd tokenmeter

# 2. Configure environment
cp .env.example .env
# Edit .env — minimum required: at least one provider API key (OPENAI_API_KEY etc),
# DATABASE_URL, CLICKHOUSE_HOST, REDIS_URL

# 3. Start infrastructure (PostgreSQL + Redis + ClickHouse)
make docker-up

# 4. Install Python dependencies
make install-backend

# 5. Initialize databases
make db-migrate       # PostgreSQL schema
make db-clickhouse    # ClickHouse schema

# 6. Start the API/proxy server
make run-backend
# Proxy available at http://localhost:8000/v1/chat/completions
# Swagger docs at http://localhost:8000/docs

# 7. (Optional) Start the dashboard
make install-frontend
make run-frontend
# Dashboard at http://localhost:3000
```

### Testing the proxy with the Python SDK

```python
import os
os.environ["TM_BASE_URL"] = "http://localhost:8000"
os.environ["TM_API_KEY"] = "local-test-key"  # Any key works in dev mode

from tokenmeter import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "Hello!"}],
    tm_team="test",
    tm_feature="dev",
)
print(f"Cost: ${response.tm_cost_usd}")
print(f"Routed to: {response.tm_provider}/{response.tm_model}")
```

---

## How to Run Tests

```bash
# Run all backend tests (with coverage)
make test

# Run backend tests only (verbose, no coverage)
make test-backend

# Run Python SDK tests
make test-sdk-python

# Run Node.js SDK tests
make test-sdk-node

# Run with full coverage report (HTML output in htmlcov/)
make test-cov

# Run a specific test file
python -m pytest tests/test_routing_engine.py -v

# Run a specific test by name
python -m pytest tests/test_routing_engine.py::test_routes_simple_query_to_cheap_model -v
```

All provider API calls are mocked in tests using `pytest-mock` or `httpx`'s test transport — no real API keys are needed to run the test suite.

---

## How the Proxy Works (Core Flow)

The main flow lives in `backend/services/proxy_handler.py`:

```
Client request (POST /v1/chat/completions)
  |
  |- Auth middleware validates API key (backend/middleware/auth.py)
  |- Rate limiter checks per-key quota (backend/middleware/rate_limiter.py)
  |
  v
proxy_handler.py::handle_request()
  |
  |- 1. Extract tm_* metadata (team, feature, routing_mode) from request
  |
  |- 2. request_classifier.py::classify(messages)
  |     Scores complexity on 8 signals:
  |       - Total message length (tokens)
  |       - Conversation depth (turn count)
  |       - Tool/function call usage
  |       - Code patterns detected (regex)
  |       - Mathematical notation
  |       - Multi-step instruction chains
  |       - Language complexity score
  |       - System prompt length
  |     Returns: ComplexityScore (0.0–1.0) + explanation
  |
  |- 3. routing_engine.py::select_model(complexity, mode, budget_remaining)
  |     Modes:
  |       cost-optimized:    cheapest model above quality threshold for complexity
  |       latency-optimized: fastest model above quality threshold
  |       quality-optimized: best model within remaining budget
  |     Returns: RoutingDecision (provider, model, reason)
  |
  |- 4. provider_registry.py::get_provider(provider_name)
  |     Returns the correct provider adapter (openai.py / anthropic.py / google.py)
  |
  |- 5. provider.forward_request(request)
  |     Translates to provider-specific API format, calls provider API
  |     Handles streaming via utils/streaming.py
  |
  |- 6. cost_calculator.py::calculate(tokens_in, tokens_out, model)
  |     Looks up per-model pricing from providers/pricing.py
  |     Returns: CostBreakdown with input_cost_usd, output_cost_usd, total_cost_usd
  |
  |- 7. usage_tracker.py::record(...)
  |     Writes to ClickHouse (time-series) + PostgreSQL (relational)
  |     Attaches team, feature, model, cost, latency
  |
  |- 8. budget_monitor.py::check_and_alert(team, feature, cost)
  |     Checks accumulated spend vs budget limits
  |     Triggers alert_service.py at 50%/80%/100% thresholds
  |
  |- 9. Return response to client with tm_* fields injected:
  |       tm_cost_usd, tm_provider, tm_model, tm_latency_ms,
  |       tm_complexity_score, tm_routing_reason
```

---

## How to Add a New LLM Provider

Adding a new provider (e.g., Mistral, Cohere, AWS Bedrock) requires 4 steps:

### Step 1: Create a provider adapter

```python
# backend/providers/mistral.py

from providers.base import BaseProvider
from models.proxy import ProxyRequest, ProxyResponse

class MistralProvider(BaseProvider):
    name = "mistral"
    base_url = "https://api.mistral.ai/v1"

    async def forward_request(self, request: ProxyRequest) -> ProxyResponse:
        # Translate ProxyRequest (OpenAI format) to Mistral API format
        # Make HTTP call using self.client (httpx.AsyncClient)
        # Translate response back to ProxyResponse (OpenAI format)
        ...

    def count_tokens(self, messages: list, model: str) -> int:
        # Use tiktoken or provider-specific tokenizer
        ...
```

### Step 2: Add pricing to the registry

```python
# backend/providers/pricing.py

MODEL_PRICING = {
    # ... existing models ...
    "mistral-large-latest": {
        "provider": "mistral",
        "input_cost_per_1m": 8.00,
        "output_cost_per_1m": 24.00,
        "context_window": 128_000,
    },
    "mistral-small-latest": {
        "provider": "mistral",
        "input_cost_per_1m": 1.00,
        "output_cost_per_1m": 3.00,
        "context_window": 128_000,
    },
}
```

### Step 3: Register the provider

```python
# backend/services/provider_registry.py

from providers.mistral import MistralProvider

# In the registry initialization:
self.providers["mistral"] = MistralProvider(api_key=settings.MISTRAL_API_KEY)
```

### Step 4: Add the API key environment variable

```bash
# .env.example (add):
MISTRAL_API_KEY=

# backend/config.py (add to Settings class):
MISTRAL_API_KEY: str = ""
```

Add tests in `tests/test_provider_mistral.py` following the pattern in `test_provider_openai.py`.

---

## Routing Engine — Complexity Signals

`backend/services/request_classifier.py` classifies each request on these 8 signals:

| Signal | Weight | How It's Detected |
|---|---|---|
| Total token count | 0.25 | tiktoken count of all messages |
| Conversation depth | 0.15 | Number of turns in messages array |
| Tool/function usage | 0.20 | Presence of `tools` or `functions` field |
| Code patterns | 0.15 | Regex: code blocks, function definitions, imports |
| Mathematical content | 0.10 | LaTeX, equations, Greek letters |
| Multi-step instructions | 0.10 | Numbered lists, "step X", "first...then..." |
| System prompt length | 0.05 | Token count of system message |

The final `ComplexityScore` (0.0–1.0) maps to model tiers:
- 0.0–0.3: Tier 1 (nano/mini models — GPT-4.1-nano, Haiku 3.5, Gemini Flash)
- 0.3–0.6: Tier 2 (mid models — GPT-4.1-mini, Sonnet 4.5, Gemini Flash)
- 0.6–0.85: Tier 3 (capable models — GPT-4.1, Sonnet 4.5)
- 0.85–1.0: Tier 4 (frontier models — GPT-5, Claude Opus 4, Gemini 2.5 Pro)

---

## How to Build and Release

```bash
# Run tests and lint before releasing
make test
make lint

# --- Backend (Fly.io) ---
# Build Docker image
make docker-build    # Produces tokenmeter-api:latest

# Deploy to Fly.io (CI/CD does this automatically on push to main)
fly deploy --config fly.toml

# --- Python SDK (PyPI) ---
# Triggered by GitHub Actions on git tag: v*.*.* for sdks/python
cd sdks/python
python setup.py sdist bdist_wheel
twine upload dist/*
# Or: push a tag and let publish-sdk-python.yml handle it

# --- Node SDK (npm) ---
# Triggered by GitHub Actions on git tag: node-v*.*.*
cd sdks/node
npm run build
npm publish
```

---

## Key Coding Patterns

1. **Provider-agnostic proxy format** — All requests are normalized to an OpenAI-compatible `ProxyRequest` shape before routing. Provider adapters translate to/from their native format. New providers just need a `forward_request()` implementation.

2. **Streaming is a first-class concern** — `utils/streaming.py` handles SSE passthrough while simultaneously counting tokens and tracking costs in the background. Never block streaming to do cost calculation.

3. **Two databases, two purposes** — PostgreSQL stores relational data (teams, features, budgets, API keys, subscriptions). ClickHouse stores the high-volume `usage_events` time-series with materialized views for fast dashboard aggregation. Do not write usage events to PostgreSQL.

4. **Budget enforcement is pre-request** — `budget_monitor.py` checks remaining budget before forwarding to the provider. If a team has `hard_limit=True` and is at 100%, the request is rejected with a 429 before any API call is made.

5. **Async everywhere** — `asyncio`, `httpx.AsyncClient` for provider calls, `asyncpg` for PostgreSQL, async ClickHouse client. Never use blocking `requests` or `psycopg2` in the request path.

6. **Zero-logging mode** — When `ZERO_LOGGING_MODE=true`, request and response body content is not stored. Only metadata (token counts, costs, model, timestamps) is recorded. This is a hard privacy guarantee for enterprise customers.

7. **The Python SDK is a thin wrapper** — `sdks/python/tokenmeter/client.py` subclasses OpenAI's `OpenAI` and overrides `_base_url` to point at the TokenMeter proxy. The `tm_*` extra kwargs are stripped from the request body and sent as HTTP headers.

8. **Pricing must be kept current** — `backend/providers/pricing.py` is a static dict. When a provider changes pricing, update this file and bump the version. The `.github/workflows/pricing-update.yml` workflow can automate this check.

9. **Linting: ruff** — configured in `pyproject.toml`. Run `make format` before committing.

---

## Common Development Tasks

### Check what model a request would be routed to

```python
from services.request_classifier import RequestClassifier
from services.routing_engine import RoutingEngine

classifier = RequestClassifier()
engine = RoutingEngine()

messages = [{"role": "user", "content": "What is 2+2?"}]
complexity = classifier.classify(messages)
print(f"Complexity: {complexity.score:.2f} — {complexity.tier}")

decision = engine.select_model(complexity, mode="cost-optimized")
print(f"Routed to: {decision.provider}/{decision.model}")
print(f"Reason: {decision.reason}")
```

### Update model pricing

Edit `backend/providers/pricing.py`. Pricing keys are model name strings matching what the provider returns in API responses.

### Add a budget for a team

```bash
curl -X POST http://localhost:8000/budgets \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "team": "search",
    "monthly_limit_usd": 500.00,
    "alert_thresholds": [50, 80, 100],
    "hard_limit": false,
    "slack_webhook_url": "https://hooks.slack.com/..."
  }'
```

### Run only routing tests

```bash
python -m pytest tests/test_routing_engine.py tests/test_request_classifier.py -v
```

---

## SDK Integration Patterns

### Python (pip install tokenmeter)

```python
from tokenmeter import OpenAI, Anthropic  # drop-in replacements

# All existing code works identically
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Explain quantum entanglement"}],
    # Optional TokenMeter metadata:
    tm_team="research",
    tm_feature="explainer",
    tm_routing_mode="quality-optimized",
)

# Extra fields on the response:
print(response.tm_cost_usd)        # 0.00312
print(response.tm_model)           # gpt-4.1 (or overridden by routing)
print(response.tm_provider)        # openai
print(response.tm_latency_ms)      # 1240
```

### HTTP (any language)

```bash
curl https://proxy.tokenmeter.dev/v1/chat/completions \
  -H "Authorization: Bearer tm_YOUR_KEY" \
  -H "X-TM-Team: search" \
  -H "X-TM-Feature: autocomplete" \
  -H "X-TM-Routing-Mode: cost-optimized" \
  -d '{"model": "gpt-4.1", "messages": [...]}'
```

---

## Architecture Summary

```
                     TokenMeter Proxy
Client SDK/HTTP
      |
      v
POST /v1/chat/completions  (backend/api/proxy.py)
      |
      |- auth middleware (API key validation)
      |- rate limiter middleware
      |
      v
proxy_handler.py
      |
      |- request_classifier.py  (8 signals -> complexity score)
      |- routing_engine.py      (complexity + mode -> model selection)
      |- provider_registry.py   (get provider adapter)
      |- provider.forward_request() (provider-specific HTTP call)
      |- cost_calculator.py     (tokens -> dollars)
      |- usage_tracker.py       (write to ClickHouse + PostgreSQL)
      |- budget_monitor.py      (check limits, trigger alerts)
      |
      v
Response with tm_* fields injected

Infrastructure:
  Fly.io (backend/proxy) + Vercel (Next.js dashboard)
  Supabase PostgreSQL + ClickHouse Cloud + Upstash Redis
  Clerk (auth) + Stripe (billing)
```
