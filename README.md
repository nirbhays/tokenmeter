<div align="center">

# TokenMeter

### The cost intelligence layer for LLM applications

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Proxy Overhead: <5ms](https://img.shields.io/badge/Overhead-<5ms-green.svg)
![Providers: OpenAI, Anthropic, Google](https://img.shields.io/badge/Providers-3-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/tokenmeter.svg)](https://pypi.org/project/tokenmeter)
[![npm](https://img.shields.io/npm/v/tokenmeter.svg)](https://www.npmjs.com/package/tokenmeter)
[![CI](https://github.com/tokenmeter/tokenmeter/actions/workflows/ci.yml/badge.svg)](https://github.com/tokenmeter/tokenmeter/actions/workflows/ci.yml)

**Know exactly what you spend on AI. Track every token. Optimize every dollar.**

[Documentation](https://docs.tokenmeter.dev) | [Dashboard Demo](https://demo.tokenmeter.dev) | [API Reference](docs/API.md)

</div>

---

## The One-Line Integration

TokenMeter works by replacing a single import. No config files, no agents, no SDKs to learn. Your existing code stays identical.

```python
# Before
from openai import OpenAI

# After
from tokenmeter import OpenAI  # That's it. Everything else stays the same.
```

Every call now automatically tracks cost, latency, tokens, and provider -- with zero changes to your application logic.

---

## Why TokenMeter?

<table>
<tr>
<td width="50%">

### Before TokenMeter

- "$4,800 AI bill. No idea which feature caused it."
- Manually estimating costs from token counts
- No visibility into per-team or per-feature spend
- Overpaying by routing every request to the most expensive model
- Finding out about cost spikes when the invoice arrives

</td>
<td width="50%">

### After TokenMeter

- Per-feature, per-team, per-model cost breakdown in real time
- Smart routing saves up to 60% by matching task complexity to model capability
- Budget alerts on Slack before you blow through limits
- Sub-5ms proxy overhead -- your users never notice
- One import change. Ship in five minutes.

</td>
</tr>
</table>

---

## Features

<table>
<tr>
<td align="center" width="25%">
<h3>Cost Tracking</h3>
<p>Real-time spend per request, team, feature, and model. Accurate to 8 decimal places.</p>
<strong>Metric: < 1s dashboard refresh</strong>
</td>
<td align="center" width="25%">
<h3>Smart Routing</h3>
<p>Automatically routes simple queries to cheap models and complex ones to powerful models.</p>
<strong>Metric: Up to 60% cost reduction</strong>
</td>
<td align="center" width="25%">
<h3>Budget Alerts</h3>
<p>Slack, webhook, and email alerts at configurable thresholds. Hard limits to block runaway spend.</p>
<strong>Metric: 50% / 80% / 100% triggers</strong>
</td>
<td align="center" width="25%">
<h3>Multi-Provider</h3>
<p>Unified interface across OpenAI, Anthropic, and Google. One SDK, three providers.</p>
<strong>Metric: 20+ models supported</strong>
</td>
</tr>
</table>

---

## Smart Routing Explained

TokenMeter classifies request complexity using 8 heuristic signals (message length, conversation depth, tool usage, code patterns, and more) then routes to the optimal model.

```
User: "What's 2+2?"
  --> Routed to GPT-4.1-mini ($0.40/1M tokens)
  --> Cost: $0.00003

User: "Refactor this 500-line module to use the strategy pattern, add types, and write tests."
  --> Routed to GPT-4.1 ($10.00/1M tokens)
  --> Cost: $0.02100

Result: The simple query cost 150x less. The complex query preserved quality.
         Average savings across production workloads: 40-60%.
```

**Three routing modes:**

| Mode | Strategy | Typical Savings |
|---|---|---|
| **Cost-Optimized** | Route to the cheapest model that can handle the task | Up to 60% |
| **Latency-Optimized** | Route to the fastest model above a quality threshold | 2-5x faster responses |
| **Quality-Optimized** | Route to the best model within a budget constraint | Maximum quality per dollar |

---

## Supported Providers

| Provider | Models | Input ($/1M tokens) | Output ($/1M tokens) |
|---|---|---|---|
| **OpenAI** | GPT-5.2, GPT-5, GPT-5-mini | $0.10 -- $12.00 | $0.40 -- $40.00 |
| | GPT-4.1, GPT-4.1-mini, GPT-4.1-nano | | |
| | o3, o4-mini | | |
| **Anthropic** | Claude Opus 4, Sonnet 4.5, Haiku 3.5 | $0.80 -- $15.00 | $4.00 -- $75.00 |
| **Google** | Gemini 2.5 Pro, Gemini 2.5 Flash | $0.15 -- $1.25 | $0.60 -- $10.00 |

Pricing is updated regularly. See [docs/PROVIDERS.md](docs/PROVIDERS.md) for the full model catalog.

---

## Quick Start

### 1. Python SDK (Recommended)

```bash
pip install tokenmeter
```

```python
from tokenmeter import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Hello!"}],
    tm_team="chatbot",        # tag for cost attribution
    tm_feature="greeting",    # which feature is this?
)

print(response.choices[0].message.content)
print(f"Cost: ${response.tm_cost_usd}")        # $0.00012
print(f"Provider: {response.tm_provider}")      # openai
print(f"Latency: {response.tm_latency_ms}ms")   # 245ms
```

### 2. Node.js SDK

```bash
npm install tokenmeter
```

```typescript
import OpenAI from 'tokenmeter';

const client = new OpenAI();
const response = await client.chat.completions.create({
  model: 'gpt-4.1',
  messages: [{ role: 'user', content: 'Hello!' }],
  tm_team: 'search',
  tm_feature: 'autocomplete',
});

console.log(`Cost: $${response.tm_cost_usd}`);
```

### 3. Direct Proxy (Any Language)

Change the base URL. Works with any OpenAI-compatible client in any language.

```bash
curl https://proxy.tokenmeter.dev/v1/chat/completions \
  -H "Authorization: Bearer tm_your_api_key" \
  -H "X-TM-Team: search" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## Architecture

```
┌──────────┐     ┌──────────────────────────────────────────┐     ┌──────────┐
│          │     │            TokenMeter Proxy               │     │  OpenAI  │
│ Your App │────>│                                           │────>│ Anthropic│
│          │<────│  ┌──────────┐ ┌────────┐ ┌────────────┐  │<────│  Google  │
│ (SDK or  │     │  │ Classify │>│ Route  │>│  Forward   │  │     └──────────┘
│  HTTP)   │     │  └──────────┘ └────────┘ └────────────┘  │
└──────────┘     │                                           │
                 │  ┌──────────┐ ┌────────┐ ┌────────────┐  │
                 │  │  Track   │ │  Cost  │ │   Cache    │  │
                 │  └─────┬────┘ └───┬────┘ └────────────┘  │
                 └────────┼──────────┼──────────────────────-┘
                          │          │
                     ┌────v────┐ ┌───v────┐ ┌────────────┐
                     │ClickHse│ │ Redis  │ │ PostgreSQL │
                     │(metrics)│ │(cache) │ │  (config)  │
                     └─────────┘ └────────┘ └─────┬──────┘
                                                   │
                                             ┌─────v──────┐
                                             │  Dashboard  │
                                             │  (Next.js)  │
                                             └────────────┘
```

**Pipeline flow:** Incoming request --> Complexity classification (8 signals) --> Model routing --> Provider forwarding --> Response tracking --> Cost attribution --> Dashboard update.

**Overhead:** < 5ms added latency. The proxy is async Python (FastAPI) with connection pooling and response streaming.

---

## Tech Stack

| Component | Technology |
|---|---|
| **Proxy / API** | Python, FastAPI, async/await |
| **Dashboard** | Next.js 14, Tailwind CSS, Recharts |
| **Relational DB** | PostgreSQL (Supabase) |
| **Time-Series DB** | ClickHouse (materialized views for fast aggregation) |
| **Cache** | Redis (Upstash) |
| **Auth** | Clerk |
| **Payments** | Stripe Billing |
| **SDKs** | Python (PyPI) + Node.js (npm) |
| **Deploy** | Fly.io (API) + Vercel (Dashboard) |
| **CI/CD** | GitHub Actions |

---

## Comparison

| Feature | TokenMeter | Helicone | Portkey | LiteLLM |
|---|:---:|:---:|:---:|:---:|
| One-line integration (import swap) | Yes | No | No | No |
| Smart routing with complexity analysis | Yes | No | Basic | Basic |
| Real-time cost dashboard | Yes | Yes | Yes | Partial |
| Budget alerts (Slack, webhook, email) | Yes | Yes | Yes | No |
| Multi-provider unified SDK | Yes | No | Yes | Yes |
| Per-feature cost attribution | Yes | Via headers | Via headers | No |
| Sub-5ms proxy overhead | Yes | ~10ms | ~15ms | ~10ms |
| Self-hosted option | Yes | Yes | No | Yes |
| Streaming support | Yes | Yes | Yes | Yes |
| Open source | MIT | Partial | No | MIT |

---

## Local Development

```bash
# 1. Clone the repo
git clone https://github.com/tokenmeter/tokenmeter
cd tokenmeter

# 2. Configure environment
cp .env.example .env
# Edit .env with your provider API keys

# 3. Start infrastructure (PostgreSQL, ClickHouse, Redis)
cd backend && docker-compose up -d

# 4. Start the API server
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload

# 5. Start the dashboard (new terminal)
cd frontend && npm install && npm run dev
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, diagrams |
| [API Reference](docs/API.md) | Complete endpoint documentation |
| [Routing Engine](docs/ROUTING-ENGINE.md) | How smart routing classifies and routes |
| [SDK Guide](docs/SDK-GUIDE.md) | Python + Node.js SDK usage and examples |
| [Providers](docs/PROVIDERS.md) | Full model catalog and pricing |
| [Deployment](docs/DEPLOYMENT.md) | Fly.io, Vercel, and database setup |
| [Development](docs/DEVELOPMENT.md) | Local setup, testing, debugging |
| [Security](docs/SECURITY.md) | Security model, encryption, zero-logging mode |

---

## Contributing

Contributions are welcome. Whether it is a bug fix, new provider integration, documentation improvement, or feature idea -- all contributions help.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run the test suite (`make test`)
5. Submit a pull request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

---

<div align="center">

**TokenMeter** is MIT licensed. Built for teams that want to ship AI without surprise invoices.

[Get Started](https://docs.tokenmeter.dev) | [View Dashboard Demo](https://demo.tokenmeter.dev) | [Star on GitHub](https://github.com/tokenmeter/tokenmeter)

</div>
