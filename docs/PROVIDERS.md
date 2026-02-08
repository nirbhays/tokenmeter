# Supported Providers & Models

## Pricing Tables (February 2026)

> Prices are in USD per 1 million tokens.

### OpenAI

| Model | Input $/1M | Output $/1M | Cached Input $/1M | Context | Quality | Speed |
|---|---:|---:|---:|---:|---:|---:|
| **GPT-5.2** | $12.00 | $40.00 | $3.00 | 256K | 0.99 | 0.60 |
| **GPT-5** | $10.00 | $30.00 | $2.50 | 256K | 0.97 | 0.65 |
| **GPT-5-mini** | $2.50 | $10.00 | $0.625 | 256K | 0.90 | 0.80 |
| **GPT-4.1** | $2.00 | $8.00 | $0.50 | 1M | 0.88 | 0.75 |
| **GPT-4.1-mini** | $0.40 | $1.60 | $0.10 | 1M | 0.82 | 0.88 |
| **GPT-4.1-nano** | $0.10 | $0.40 | $0.025 | 1M | 0.72 | 0.95 |
| **o3** | $10.00 | $40.00 | $2.50 | 200K | 0.97 | 0.40 |
| **o4-mini** | $1.10 | $4.40 | $0.275 | 200K | 0.92 | 0.55 |

**Embeddings:**

| Model | Input $/1M | Context |
|---|---:|---:|
| text-embedding-3-large | $0.13 | 8,191 |
| text-embedding-3-small | $0.02 | 8,191 |

### Anthropic

| Model | Input $/1M | Output $/1M | Cached Input $/1M | Context | Quality | Speed |
|---|---:|---:|---:|---:|---:|---:|
| **Claude Opus 4** | $15.00 | $75.00 | $1.875 | 200K | 0.98 | 0.50 |
| **Claude Sonnet 4.5** | $3.00 | $15.00 | $0.375 | 200K | 0.93 | 0.75 |
| **Claude Haiku 3.5** | $0.80 | $4.00 | $0.08 | 200K | 0.82 | 0.92 |

### Google

| Model | Input $/1M | Output $/1M | Cached Input $/1M | Context | Quality | Speed |
|---|---:|---:|---:|---:|---:|---:|
| **Gemini 2.5 Pro** | $1.25 | $10.00 | $0.3125 | 1M | 0.95 | 0.65 |
| **Gemini 2.5 Flash** | $0.15 | $0.60 | $0.0375 | 1M | 0.86 | 0.92 |

## Model Capabilities

| Capability | GPT-5.2 | GPT-4.1-nano | Claude Opus 4 | Gemini Flash |
|---|:---:|:---:|:---:|:---:|
| Chat | ✅ | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ | ✅ |
| Function Calling | ✅ | ❌ | ✅ | ✅ |
| Vision | ✅ | ❌ | ✅ | ✅ |
| JSON Mode | ✅ | ✅ | ✅ | ✅ |

## Cost Comparison Example

For a typical chatbot handling 100K requests/month:

| Strategy | Model Mix | Monthly Cost |
|---|---|---:|
| All GPT-5 | 100% GPT-5 | $4,000 |
| All GPT-4.1 | 100% GPT-4.1 | $800 |
| **TokenMeter Smart** | 60% nano, 30% mini, 10% GPT-4.1 | **$160** |
| Savings | | **96%** |
