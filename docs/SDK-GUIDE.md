# SDK Guide

TokenMeter provides drop-in replacement SDKs for Python and Node.js. Change one import and all your LLM calls are tracked, costed, and routed.

## Python SDK

### Installation

```bash
pip install tokenmeter
```

### Basic Usage

```python
# ONE LINE CHANGE
from tokenmeter import OpenAI  # instead of: from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Hello!"}],
)

# Standard OpenAI fields
print(response.choices[0].message.content)
print(response.usage.total_tokens)

# TokenMeter additions
print(f"Cost: ${response.tm_cost_usd}")
print(f"Provider: {response.tm_provider}")
print(f"Latency: {response.tm_latency_ms}ms")
```

### Streaming

```python
stream = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Write a story"}],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

### Cost Attribution

```python
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Summarize this"}],
    tm_team="search",           # Shows up in dashboard as "search" team
    tm_feature="auto-summarize", # Shows up as "auto-summarize" feature
)
```

### Routing Override

```python
# Force cost-optimized routing (may downgrade model)
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    tm_routing_mode="cost-optimized",
)
print(f"Routed from: {response.tm_routed_from}")  # "gpt-4.1" → actually used gpt-4.1-nano
```

### Configuration

```python
client = OpenAI(
    api_key="tm_your_key",                          # or TOKENMETER_API_KEY env var
    base_url="https://proxy.tokenmeter.dev",         # or TOKENMETER_BASE_URL env var
    timeout=120.0,
)
```

---

## Node.js SDK

### Installation

```bash
npm install tokenmeter
```

### Basic Usage

```typescript
// ONE LINE CHANGE
import OpenAI from 'tokenmeter';  // instead of: import OpenAI from 'openai'

const client = new OpenAI();

const response = await client.chat.completions.create({
  model: 'gpt-4.1',
  messages: [{ role: 'user', content: 'Hello!' }],
});

console.log(response.choices[0].message.content);
console.log(`Cost: $${response.tm_cost_usd}`);
console.log(`Provider: ${response.tm_provider}`);
```

### Streaming

```typescript
const stream = await client.chat.completions.create({
  model: 'gpt-4.1',
  messages: [{ role: 'user', content: 'Write a poem' }],
  stream: true,
});

for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content;
  if (content) process.stdout.write(content);
}
```

### Cost Attribution

```typescript
const response = await client.chat.completions.create({
  model: 'gpt-4.1',
  messages: [{ role: 'user', content: 'Search query' }],
  tm_team: 'search',
  tm_feature: 'semantic-search',
});
```

### Configuration

```typescript
const client = new OpenAI({
  apiKey: 'tm_your_key',                   // or TOKENMETER_API_KEY
  baseUrl: 'https://proxy.tokenmeter.dev', // or TOKENMETER_BASE_URL
  timeout: 120000,
});
```

---

## Direct HTTP (Any Language)

If you're not using Python or Node.js, just change the base URL:

```bash
# Go
client := openai.NewClient(
    option.WithBaseURL("https://proxy.tokenmeter.dev/v1"),
    option.WithAPIKey("tm_your_key"),
)

# Ruby
OpenAI.configure do |config|
  config.uri_base = "https://proxy.tokenmeter.dev/v1"
  config.access_token = "tm_your_key"
end

# curl
curl https://proxy.tokenmeter.dev/v1/chat/completions \
  -H "Authorization: Bearer tm_your_key" \
  -H "X-TM-Team: my-team" \
  -d '{"model": "gpt-4.1", "messages": [{"role": "user", "content": "hi"}]}'
```
