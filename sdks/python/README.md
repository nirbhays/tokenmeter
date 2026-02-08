# TokenMeter Python SDK

Drop-in replacement for the OpenAI Python client with **automatic cost tracking, smart routing, and budget alerts**.

## Installation

```bash
pip install tokenmeter
```

## Quick Start

Change **one line** of code:

```python
# Before
from openai import OpenAI

# After
from tokenmeter import OpenAI

client = OpenAI()  # Uses TOKENMETER_API_KEY env var

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Hello!"}],
)

print(response.choices[0].message.content)
print(f"Cost: ${response.tm_cost_usd}")       # ← cost tracking
print(f"Latency: {response.tm_latency_ms}ms") # ← latency tracking
print(f"Provider: {response.tm_provider}")     # ← which provider was used
```

## Streaming

```python
from tokenmeter import OpenAI

client = OpenAI()

stream = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## Cost Attribution

Tag requests with team and feature for cost breakdowns:

```python
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Summarize this document"}],
    tm_team="search",
    tm_feature="auto-summarize",
)
```

## Smart Routing

Override the routing mode per request:

```python
# Use the cheapest model that can handle this query
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    tm_routing_mode="cost-optimized",  # Routes to gpt-4.1-nano
)
```

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `TOKENMETER_API_KEY` | — | Your TokenMeter API key (`tm_...`) |
| `TOKENMETER_BASE_URL` | `http://localhost:8000` | TokenMeter proxy URL |
| `OPENAI_API_KEY` | — | Fallback if TOKENMETER_API_KEY not set |

## License

MIT
