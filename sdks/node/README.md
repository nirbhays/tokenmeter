# TokenMeter Node.js SDK

Drop-in replacement for the OpenAI Node.js client with **automatic cost tracking, smart routing, and budget alerts**.

## Installation

```bash
npm install tokenmeter
```

## Quick Start

Change **one line** of code:

```typescript
// Before
import OpenAI from 'openai';

// After
import OpenAI from 'tokenmeter';

const client = new OpenAI();

const response = await client.chat.completions.create({
  model: 'gpt-4.1',
  messages: [{ role: 'user', content: 'Hello!' }],
});

console.log(response.choices[0].message.content);
console.log(`Cost: $${response.tm_cost_usd}`);       // ← cost tracking
console.log(`Latency: ${response.tm_latency_ms}ms`); // ← latency tracking
console.log(`Provider: ${response.tm_provider}`);     // ← which provider
```

## Streaming

```typescript
import OpenAI from 'tokenmeter';

const client = new OpenAI();

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

## Cost Attribution

```typescript
const response = await client.chat.completions.create({
  model: 'gpt-4.1',
  messages: [{ role: 'user', content: 'Summarize this' }],
  tm_team: 'search',
  tm_feature: 'auto-summarize',
});
```

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `TOKENMETER_API_KEY` | — | Your TokenMeter API key |
| `TOKENMETER_BASE_URL` | `http://localhost:8000` | TokenMeter proxy URL |
| `OPENAI_API_KEY` | — | Fallback API key |

## License

MIT
