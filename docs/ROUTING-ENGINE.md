# Smart Routing Engine

## Overview

TokenMeter's Smart Routing Engine automatically selects the best model for each request based on complexity analysis. This can save up to 60% on AI costs by routing simple queries to cheap, fast models.

## How It Works

### Step 1: Request Classification

Every incoming request is analyzed across 8 signals to produce a complexity score (0.0 - 1.0):

```
Score: 0.0 ────────── 0.25 ────────── 0.55 ────────── 1.0
       │    SIMPLE     │    MEDIUM     │    COMPLEX    │
       │               │               │               │
       │ gpt-4.1-nano  │ gpt-4.1-mini │  gpt-5.2     │
       │ $0.10/1M      │ $0.40/1M     │  $12.00/1M   │
```

### Signal Weights

| Signal | Max Weight | Examples |
|---|---|---|
| **Message length** | ±0.25 | >5000 chars = +0.25, <200 chars = -0.10 |
| **Conversation depth** | +0.15 | >5 turns = +0.15, 1 turn = -0.05 |
| **System prompt** | +0.15 | >2000 chars = +0.15 |
| **Tool/function calls** | +0.30 | Tools defined = +0.20, tool calls in history = +0.10 |
| **Keyword analysis** | ±0.25 | "analyze", "implement", "refactor" = complex; "translate", "summarize" = simple |
| **Output length** | ±0.15 | max_tokens > 4000 = +0.15, < 100 = -0.10 |
| **Response format** | +0.05 | JSON mode = +0.05 |
| **Code patterns** | +0.15 | Code blocks, imports, class definitions |

### Step 2: Routing Mode

Three built-in routing modes determine which model to use:

#### Cost-Optimized (Default)

| Complexity | Primary Model | Fallbacks |
|---|---|---|
| Simple | gpt-4.1-nano ($0.10/1M) | gemini-2.5-flash, claude-haiku-3.5 |
| Medium | gpt-4.1-mini ($0.40/1M) | gpt-4.1, claude-sonnet-4.5 |
| Complex | gpt-4.1 ($2.00/1M) | gpt-5, claude-sonnet-4.5 |

#### Latency-Optimized

| Complexity | Primary Model | Speed Score |
|---|---|---|
| Simple | gpt-4.1-nano | 0.95 |
| Medium | gpt-4.1-mini | 0.88 |
| Complex | gpt-4.1 | 0.75 |

#### Quality-Optimized

| Complexity | Primary Model | Quality Score |
|---|---|---|
| Simple | gpt-4.1-mini | 0.82 |
| Medium | gpt-5 | 0.97 |
| Complex | gpt-5.2 | 0.99 |

### Step 3: Custom Rules

Custom rules are evaluated before automatic classification and take priority:

```json
{
  "name": "Search team uses Flash",
  "priority": 100,
  "teams": ["search"],
  "target_model": "gemini-2.5-flash"
}
```

Rules can match on:
- Source models
- Complexity levels
- Team tags
- Feature tags
- Token thresholds

### Step 4: Fallback Chain

If the selected model is unavailable, TokenMeter follows the fallback chain:

```
gpt-5.2 → gpt-5 → gpt-4.1 → gpt-4.1-mini → gpt-4.1-nano
```

## Examples

### Example 1: Simple Classification

```
User: "What is 2+2?"
→ Signals: short_input(13), 1 turn, no tools, simple keywords
→ Score: 0.05 (SIMPLE)
→ Route: gpt-4.1-nano ($0.10/1M)
→ Cost: $0.0000052 instead of $0.0000800 (GPT-4.1)
→ Savings: 93%
```

### Example 2: Complex Code Review

```
User: "Review this 500-line Python module, identify anti-patterns,
       and provide a refactoring plan with examples..."
System: "You are an expert software architect..."
Tools: [search_codebase, run_tests]
→ Signals: long_input(5200), complex_system(2100), tools(2), code(4), complex_keywords(6)
→ Score: 0.82 (COMPLEX)
→ Route: gpt-5.2 ($12.00/1M) — quality mode
```

## Configuration

### Via API

```bash
# Set routing mode
curl -X PUT /api/routing/config \
  -d '{"mode": "cost-optimized", "enabled": true}'

# Add custom rule
curl -X POST /api/routing/rules \
  -d '{
    "name": "Chatbot → Haiku",
    "teams": ["chatbot"],
    "complexity_levels": ["simple"],
    "target_model": "claude-haiku-3.5"
  }'
```

### Via SDK

```python
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[...],
    tm_routing_mode="cost-optimized",  # Override per-request
)
```
