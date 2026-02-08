# API Reference

## Overview

TokenMeter exposes two categories of endpoints:

1. **Proxy Endpoints** (`/v1/...`) — OpenAI-compatible API that forwards to LLM providers
2. **Dashboard Endpoints** (`/api/...`) — Management APIs for the dashboard

All endpoints require authentication via Bearer token (API key).

**Base URL**: `https://proxy.tokenmeter.dev` (or `http://localhost:8000` for local dev)

---

## Authentication

All requests must include an API key:

```
Authorization: Bearer tm_your_api_key_here
```

---

## Proxy Endpoints

### POST /v1/chat/completions

OpenAI-compatible chat completions. Supports streaming (SSE).

**Request Body:**

```json
{
  "model": "gpt-4.1",
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false,
  "tools": [],
  "response_format": {"type": "text"}
}
```

**TokenMeter Extension Headers:**

| Header | Type | Description |
|---|---|---|
| `X-TM-Team` | string | Team tag for cost attribution |
| `X-TM-Feature` | string | Feature tag for cost attribution |
| `X-TM-Routing-Mode` | string | Override routing: `cost-optimized`, `latency-optimized`, `quality-optimized` |

**Response (non-streaming):**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1707350400,
  "model": "gpt-4.1",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "Hello! How can I help?"},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 8,
    "total_tokens": 23
  },
  "tm_provider": "openai",
  "tm_cost_usd": 0.0000344,
  "tm_latency_ms": 245.3,
  "tm_cached": false,
  "tm_routed_from": null
}
```

**Response (streaming):**

```
data: {"id":"chatcmpl-abc","object":"chat.completion.chunk","model":"gpt-4.1","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc","object":"chat.completion.chunk","model":"gpt-4.1","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc","object":"chat.completion.chunk","model":"gpt-4.1","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":"stop"}],"usage":{"prompt_tokens":15,"completion_tokens":2,"total_tokens":17}}

data: [DONE]
```

### POST /v1/embeddings

OpenAI-compatible embeddings endpoint.

**Request:**

```json
{
  "model": "text-embedding-3-small",
  "input": "Hello world"
}
```

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0023, -0.009, ...],
      "index": 0
    }
  ],
  "model": "text-embedding-3-small",
  "usage": {"prompt_tokens": 2, "total_tokens": 2},
  "tm_provider": "openai",
  "tm_cost_usd": 0.00000004,
  "tm_latency_ms": 89.2
}
```

### GET /v1/models

List available models.

---

## Dashboard Endpoints

### GET /api/dashboard/overview

Complete dashboard data with all analytics.

**Query Parameters:**

| Param | Default | Description |
|---|---|---|
| `period` | `24h` | Time period: `1h`, `24h`, `7d`, `30d`, `90d` |
| `team` | — | Filter by team |
| `feature` | — | Filter by feature |
| `model` | — | Filter by model |
| `granularity` | `hour` | `minute`, `hour`, `day`, `week` |

### GET /api/dashboard/cost-trend

Time-series cost data.

### GET /api/dashboard/model-breakdown

Cost breakdown by model.

### GET /api/dashboard/team-breakdown

Cost breakdown by team.

---

## Budget Endpoints

### GET /api/budgets/

List all budgets.

### POST /api/budgets/

Create a budget.

```json
{
  "name": "Monthly AI Spend",
  "amount_usd": 500.0,
  "period": "monthly",
  "team": null,
  "hard_limit": false,
  "thresholds": [
    {"percentage": 50, "severity": "info", "channels": ["slack"]},
    {"percentage": 80, "severity": "warning", "channels": ["slack"]},
    {"percentage": 100, "severity": "critical", "channels": ["slack", "email"]}
  ]
}
```

### GET /api/budgets/{id}

Get budget status with utilization and projected spend.

### PUT /api/budgets/{id}

Update a budget.

### DELETE /api/budgets/{id}

Delete a budget.

---

## Routing Endpoints

### GET /api/routing/config

Get routing configuration.

### PUT /api/routing/config

Update routing mode, aliases, fallbacks.

```json
{
  "mode": "cost-optimized",
  "enabled": true,
  "model_aliases": {"gpt-4": "gpt-4.1"},
  "fallback_models": {"gpt-5.2": ["gpt-5", "gpt-4.1"]}
}
```

### POST /api/routing/rules

Create a custom routing rule.

### GET /api/routing/models

List all available models with pricing.

---

## API Key Endpoints

### GET /api/keys/

List API keys (masked).

### POST /api/keys/

Create a new API key. Returns the full key **once**.

### DELETE /api/keys/{id}

Revoke an API key.

---

## Error Responses

All errors follow the OpenAI error format:

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": "invalid_api_key"
  }
}
```

| Status | Type | Description |
|---|---|---|
| 401 | `authentication_error` | Invalid or missing API key |
| 429 | `rate_limit_error` | Rate limit exceeded |
| 429 | `budget_exceeded` | Hard budget limit reached |
| 502 | `proxy_error` | Upstream provider error |
| 503 | `provider_unavailable` | No provider configured for model |
