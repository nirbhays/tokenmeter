# Our AI Bill Was $4,800 Last Month. Nobody Knew Why. So I Built an Open-Source LLM Cost Tracker.

*How I built a drop-in proxy that turned our LLM spending from a black box into a real-time dashboard -- and cut costs by 60%. A complete guide to tracking and optimizing OpenAI, Anthropic, and Google AI API costs in 2026.*

---

February's AI invoice arrived: **$4,800**. Up from $1,200 in January. Four times the cost in four weeks.

We had 14 microservices calling GPT-4. Nobody owned the bill. Nobody knew which feature was responsible for 60% of the spend.

I called a meeting. "Who can tell me why we went from $1,200 to $4,800?" Silence. The search team thought it might be them. The chatbot team pointed at the new summarization feature. The intern swore his agent prototype was only running in staging. Spoiler: it was not.

It took me two days of digging through OpenAI's usage dashboard -- which gives you a single aggregated number, no breakdown by feature, no breakdown by team, no breakdown by anything useful -- to piece together the answer. Forty percent of the bill was a single autocomplete endpoint. One developer had hardcoded `gpt-5.2` when `gpt-4.1-nano` would have produced identical results for that use case. The remaining spike was the intern's agent, which had leaked to production with a retry loop that hammered GPT-5 eight times per failed request.

**$3,600 wasted. Completely invisible until the invoice landed.**

That was the moment I decided to build TokenMeter.

---

## The AI Cost Crisis Nobody Talks About

Here is a number that should alarm every engineering leader: the average mid-size company using LLMs in production spends between **$2,000 and $25,000 per month** on API calls, and that number is growing 30-40% quarter over quarter as teams ship more AI features.

The terrifying part is not the spend itself. It is the **complete absence of visibility**.

Think about this: your cloud infrastructure bill comes with resource-level cost allocation, tagging, alerts, anomaly detection, and reserved capacity planning. AWS, GCP, and Azure have invested billions in making cloud costs transparent and manageable.

Your LLM bill? You get a number. Maybe a bar chart.

- **OpenAI**: aggregated usage by day. No per-feature breakdown. No per-team allocation. No real-time alerts.
- **Anthropic**: basic usage dashboard. No cost-per-request granularity. No budget enforcement.
- **Google AI**: buried inside the GCP billing console. Requires a PhD in Cloud Console navigation to find anything.

And if you are using multiple providers -- which most production teams are -- you are reconciling three separate billing systems with three separate dashboards using three separate date formats. Good luck figuring out which feature costs what.

The industry has a name for this in cloud computing: **shadow IT spend**. The AI version is worse because the cost per request varies by **120x** depending on which model you call, and most developers have no idea what their code is spending.

I built TokenMeter to solve exactly this problem. It is an open-source proxy that sits between your application and every LLM provider. It tracks every token, every dollar, every millisecond. It routes cheap queries to cheap models automatically. It kills requests when budgets run dry. And it takes **one line of code to integrate**.

Let me show you how it works -- and then let me show you the code.

---

## How to Track OpenAI API Costs: The One-Line Integration

Here is the entire migration. I am not exaggerating.

```python
# Before -- direct OpenAI calls, zero cost visibility
from openai import OpenAI

# After -- full cost tracking, smart routing, budget enforcement
from tokenmeter import OpenAI
```

That is it. One import change. Your existing code -- every `client.chat.completions.create()` call, every streaming response, every tool call -- **it all keeps working identically**. TokenMeter's SDK is a transparent wrapper around the official OpenAI client. Same API surface. Zero breaking changes.

Under the hood, the `TokenMeterClient` speaks the same protocol as the official OpenAI SDK, routing every request through the proxy:

```python
class TokenMeterClient:
    """
    Drop-in replacement for the OpenAI Python client.

    Usage:
        from tokenmeter import OpenAI
        client = OpenAI()
    """

    def __init__(self, *, api_key=None, base_url=None, timeout=120.0, max_retries=2):
        self.api_key = api_key or os.environ.get("TOKENMETER_API_KEY", "")
        self.base_url = (base_url or os.environ.get("TOKENMETER_BASE_URL",
                         "http://localhost:8000")).rstrip("/")

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "tokenmeter-python/0.1.0",
            },
            timeout=httpx.Timeout(self.timeout),
        )
        # API namespaces -- identical to OpenAI
        self.chat = Chat(self)
        self.models = Models(self)
```

Now every request flows through TokenMeter's proxy, and suddenly you get *this* back:

```python
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Hello!"}],
    tm_team="chatbot",       # Tag with team
    tm_feature="greeting",   # Tag with feature
)

print(f"Cost: ${response.tm_cost_usd}")       # $0.00012
print(f"Provider: {response.tm_provider}")     # openai
print(f"Latency: {response.tm_latency_ms}ms")  # 245ms
print(f"Cached: {response.tm_cached}")         # False
print(f"Routed from: {response.tm_routed_from}") # gpt-4.1 (or None if not rerouted)
```

Every single response now carries **cost, provider, latency, and routing metadata**. Tag requests with `tm_team` and `tm_feature` and you instantly know: the chatbot team's greeting feature costs $12/day through OpenAI. That search autocomplete running Claude Sonnet? $180/day. The intern's experimental agent using GPT-5.2 with 8 tool definitions? **$47 per hour**.

No more mystery invoices. No more "which feature is this?"

The Node.js SDK works the same way:

```typescript
import { OpenAI } from 'tokenmeter';

const client = new OpenAI();
const response = await client.chat.completions.create({
    model: 'gpt-4.1',
    messages: [{ role: 'user', content: 'Hello!' }],
    tm_team: 'chatbot',
    tm_feature: 'greeting',
});

console.log(`Cost: $${response.tm_cost_usd}`);
```

---

## Inside the Proxy: How Every Request Gets Tracked

When a request hits TokenMeter, it flows through a pipeline that adds **less than 5ms of overhead** at p99. Here is what happens in those milliseconds:

**Auth --> Budget Check --> Cache --> Classify --> Route --> Forward --> Track**

This is the core of the system -- the `ProxyHandler` class that orchestrates the full lifecycle:

```python
class ProxyHandler:
    """
    Handles the full lifecycle of a proxied LLM API request:

    1. Check budget hard limits
    2. Check cache
    3. Classify complexity + route
    4. Forward to provider (streaming or non-streaming)
    5. Calculate cost
    6. Track usage (async buffer --> ClickHouse)
    7. Record budget spend + trigger alerts
    """

    async def handle_chat_completion(self, request, *, org_id, api_key_id,
                                     routing_config=None):
        start_time = time.perf_counter()

        # Step 1: Check budget hard limits FIRST -- fail fast
        exceeded = self.budget.check_hard_limit(org_id, team=request.tm_team,
                                                 feature=request.tm_feature)
        if exceeded:
            raise BudgetExceededError(
                f"Budget '{exceeded.name}' exceeded: "
                f"${exceeded.current_spend_usd:.2f} / ${exceeded.amount_usd:.2f}"
            )

        # Step 2: Cache check (non-streaming only)
        if not request.stream:
            cached = await self.cache.get(request)
            if cached:
                cached.tm_cached = True
                return cached

        # Step 3: Classify and route
        engine = RoutingEngine(available_models=self._get_available_models())
        decision = engine.route(request, routing_config)

        # Step 4: Forward to the chosen provider
        provider = self.registry.get_provider_for_model(decision.routed_model)
        routed_request = request.model_copy(update={"model": decision.routed_model})

        if request.stream:
            return self._handle_streaming(routed_request, decision, provider, ...)
        else:
            response = await provider.chat_completion(routed_request)

            # Step 5: Calculate cost
            cost = self.cost_calc.calculate(
                decision.routed_model,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
            )
            response.tm_cost_usd = cost.total_cost_usd

            # Step 6: Track usage (async -- does NOT block response)
            await self.tracker.track(record)

            return response
```

The critical design choice: **everything after forwarding is async**. Cost calculation, usage tracking, budget recording -- none of it blocks the response back to your application. The proxy calculates cost from the provider's response, buffers it in memory, and flushes to ClickHouse in batches. Your users never wait for our bookkeeping.

Streaming works too. TokenMeter wraps the SSE stream with accumulator callbacks:

```python
async def _handle_streaming(self, routed_request, decision, provider, ...):
    prompt_tokens = count_message_tokens(routed_request.messages, routed_request.model)
    completion_tokens = 0
    first_token_time = None

    async def on_chunk(chunk):
        nonlocal completion_tokens, first_token_time
        if first_token_time is None:
            first_token_time = time.perf_counter()
        for choice in chunk.choices:
            if choice.delta.content:
                completion_tokens += 1  # 1 chunk ~ 1 token

    async def on_done():
        # Calculate cost and track usage AFTER stream completes
        cost = self.cost_calc.calculate(decision.routed_model,
                                         prompt_tokens, completion_tokens)
        await self.tracker.track(record)

    chunks = provider.chat_completion_stream(routed_request)
    return sse_generator(chunks, on_chunk=on_chunk, on_done=on_done)
```

Every SSE chunk passes through to the client untouched. The `on_chunk` callback counts tokens as they fly by. The `on_done` callback fires after `[DONE]`, calculates cost, and submits the usage record to the async buffer. Your users see the first token just as fast as they would hitting the provider directly.

---

## LLM Cost Optimization Guide 2026: Smart Routing That Pays for Itself

This is the feature that gets people excited. And honestly, it is the reason I built TokenMeter in the first place.

Here is the insight: **most LLM requests do not need a frontier model.**

Let me walk through a real example. A user types "translate hello to Spanish" in your app. Here is what happens:

1. The request hits TokenMeter. The classifier scans it: **50 input tokens, no system prompt, no tools, no code patterns, keyword "translate" matches the simple keyword set**.
2. Complexity score: **0.05** (well below the 0.25 threshold for "simple").
3. The router selects `gpt-4.1-nano` ($0.10/M input tokens) instead of the requested `gpt-4.1` ($2.00/M input tokens).
4. Cost for this request: **$0.000005** instead of **$0.0001**. Twenty times cheaper.
5. At 10,000 requests per day, that single routing decision saves **$0.95/day per endpoint**, or **$28.50/month**.

Now multiply that across every simple request in your system -- classification, extraction, translation, formatting, FAQ lookups. When 70% of your traffic is simple queries being served by a model that costs 20-120x less, the savings compound fast.

Here is the actual classification algorithm. Eight heuristic signals, no LLM calls, sub-millisecond execution:

```python
class RequestClassifier:
    """Classifies request complexity using 8 heuristic signals."""

    @staticmethod
    def classify(request: ChatCompletionRequest) -> tuple[ComplexityLevel, float]:
        score = 0.0

        # Signal 1: Total message length
        total_chars = sum(len(m.content) for m in request.messages if m.content)
        if total_chars > 5000:    score += 0.25   # Long input = complex
        elif total_chars > 1500:  score += 0.15
        elif total_chars < 200:   score -= 0.1    # Short input = simple

        # Signal 2: Conversation depth
        user_turns = len([m for m in request.messages if m.role == "user"])
        if user_turns > 5:   score += 0.15  # Deep conversation = harder context
        elif user_turns == 1: score -= 0.05

        # Signal 3: System prompt complexity
        sys_len = sum(len(m.content) for m in request.messages if m.role == "system")
        if sys_len > 2000:  score += 0.15  # Complex system prompt = nuanced task
        elif sys_len > 500: score += 0.05

        # Signal 4: Tool/function calling
        if request.tools and len(request.tools) > 0:
            score += 0.2  # Tools = agentic complexity

        # Signal 5: Keyword analysis
        all_text = " ".join(m.content.lower() for m in request.messages if m.content)
        complex_hits = sum(1 for kw in COMPLEX_KEYWORDS if kw in all_text)
        simple_hits = sum(1 for kw in SIMPLE_KEYWORDS if kw in all_text)
        if complex_hits > 3:  score += 0.25
        if simple_hits > 2:   score -= 0.15

        # Signal 6: Requested output length
        if request.max_tokens and request.max_tokens > 4000:  score += 0.15
        if request.max_tokens and request.max_tokens < 100:   score -= 0.1

        # Signal 7: JSON mode / structured output
        if request.response_format and request.response_format.type != "text":
            score += 0.05

        # Signal 8: Code patterns in content
        code_patterns = [r"```", r"def\s+\w+", r"class\s+\w+", r"import\s+"]
        code_hits = sum(1 for p in code_patterns if re.search(p, all_text))
        if code_hits >= 3: score += 0.15

        # Clamp 0.0-1.0 and classify
        score = max(0.0, min(1.0, score))
        if score >= 0.55:   return ComplexityLevel.complex, score
        elif score >= 0.25: return ComplexityLevel.medium, score
        else:               return ComplexityLevel.simple, score
```

The keyword sets are carefully tuned. `COMPLEX_KEYWORDS` includes terms like "analyze", "implement", "refactor", "algorithm", "prove", "step-by-step" -- words that signal genuine reasoning work. `SIMPLE_KEYWORDS` includes "translate", "summarize", "classify", "extract", "yes or no" -- tasks any model handles well.

The complexity score maps to three tiers, each with a preferred model chain:

| Tier | Score | Cost-Optimized Models | Price Range |
|---|---|---|---|
| **Simple** | < 0.25 | `gpt-4.1-nano`, `gemini-2.5-flash`, `claude-haiku-3.5` | $0.10 - $0.80/M tokens |
| **Medium** | 0.25 - 0.55 | `gpt-4.1-mini`, `gpt-4.1`, `claude-sonnet-4.5` | $0.40 - $3.00/M tokens |
| **Complex** | >= 0.55 | `gpt-4.1`, `gpt-5`, `claude-sonnet-4.5`, `gemini-2.5-pro` | $2.00 - $12.00/M tokens |

And you get three routing modes:

```python
COST_OPTIMIZED_MAP = {
    ComplexityLevel.simple:  ["gpt-4.1-nano", "gemini-2.5-flash", "claude-haiku-3.5"],
    ComplexityLevel.medium:  ["gpt-4.1-mini", "gpt-4.1", "claude-sonnet-4.5"],
    ComplexityLevel.complex: ["gpt-4.1", "gpt-5", "claude-sonnet-4.5", "gemini-2.5-pro"],
}

LATENCY_OPTIMIZED_MAP = {
    ComplexityLevel.simple:  ["gpt-4.1-nano", "gemini-2.5-flash"],
    ComplexityLevel.medium:  ["gpt-4.1-mini", "gemini-2.5-flash", "claude-haiku-3.5"],
    ComplexityLevel.complex: ["gpt-4.1", "gpt-5-mini", "claude-sonnet-4.5"],
}

QUALITY_OPTIMIZED_MAP = {
    ComplexityLevel.simple:  ["gpt-4.1-mini", "claude-sonnet-4.5"],
    ComplexityLevel.medium:  ["gpt-5", "claude-sonnet-4.5", "gemini-2.5-pro"],
    ComplexityLevel.complex: ["gpt-5.2", "claude-opus-4", "o3"],
}
```

Switch modes per-request (`tm_routing_mode="latency-optimized"`) or globally per-team. Want cost savings on your FAQ bot but maximum quality on your code review agent? Configure both independently.

In practice, on mixed production workloads: **up to 60% cost savings** without quality degradation on simple requests. The "translate this sentence" and "extract the email from this text" queries that make up the bulk of most apps' traffic? They cost pennies instead of dollars.

---

## ClickHouse vs PostgreSQL: Why We Use Both

This is a decision I get asked about a lot, so let me walk through the reasoning with real numbers.

Early on, I logged everything to PostgreSQL. It worked fine at 100 requests per day. At 10,000 requests per day, the dashboard query "show me total cost per model for the last 30 days" took **8.2 seconds**. At 100,000 requests per day -- which is only about 1.2 requests per second -- the same query **timed out at 30 seconds**.

The problem is fundamental. PostgreSQL is **row-oriented**. To answer "total cost per model for 30 days," it reads every column of every row -- the request ID, the timestamp, the team name, the feature name, the tokens, the latency, the error message -- just to sum two columns: `model` and `cost_usd`. On a table with 3 million rows and 25 columns, that is a lot of wasted I/O.

ClickHouse is **column-oriented**. That same query reads only the `routed_model` and `cost_usd` columns. On 3 million rows, that is two columns instead of 25 -- roughly **12x less data** to scan. With ClickHouse's compression (which gets 10-20x ratios on repetitive string columns like model names), the actual I/O reduction is more like **100x**.

Real numbers from my testing:

| Query | PostgreSQL (3M rows) | ClickHouse (3M rows) | Speedup |
|---|---|---|---|
| Total cost by model, 30 days | 8.2s | 45ms | **182x** |
| Hourly cost trend, 7 days | 4.1s | 22ms | **186x** |
| Top 10 features by spend | 6.8s | 38ms | **179x** |
| P95 latency by provider | 12.4s | 61ms | **203x** |

But I did not want to give up PostgreSQL entirely. It is the right tool for relational data: users, organizations, API keys, routing rules, budget configurations, Stripe subscriptions. Data with foreign key relationships, UNIQUE constraints, transactional updates. ClickHouse does not even support UPDATE or DELETE in the traditional sense.

So TokenMeter uses **both**, each for what it does best:

**PostgreSQL (Supabase)** -- the system of record:

```sql
-- Users, orgs, API keys, routing rules, budgets, subscriptions
-- Foreign keys, UNIQUE constraints, ACID transactions
CREATE TABLE api_keys (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL DEFAULT 'default',
    key_hash     VARCHAR(128) NOT NULL UNIQUE,
    key_prefix   VARCHAR(20) NOT NULL,
    scopes       TEXT[] DEFAULT ARRAY['proxy', 'dashboard'],
    revoked      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**ClickHouse** -- the analytics engine:

```sql
CREATE TABLE request_logs (
    id                      String,
    timestamp               DateTime64(3, 'UTC'),
    org_id                  String,
    team                    String DEFAULT '',
    feature                 String DEFAULT '',
    requested_model         String,
    routed_model            String,
    provider                String,
    prompt_tokens           UInt32 DEFAULT 0,
    completion_tokens       UInt32 DEFAULT 0,
    cost_usd                Float64 DEFAULT 0,
    input_cost_usd          Float64 DEFAULT 0,
    output_cost_usd         Float64 DEFAULT 0,
    latency_ms              Float64 DEFAULT 0,
    time_to_first_token_ms  Float64 DEFAULT 0,
    status                  String DEFAULT 'success',
    routing_mode            String DEFAULT '',
    complexity_score        Float32 DEFAULT 0,
    cached                  UInt8 DEFAULT 0
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (org_id, timestamp, id)
TTL timestamp + INTERVAL 365 DAY;
```

The ClickHouse schema includes **four materialized views** that pre-aggregate data for the dashboard. When you open the dashboard and ask "what did we spend last week by model?", it reads from a table that already has the answer -- no full table scan, no GROUP BY across millions of rows:

```sql
-- Pre-aggregated hourly stats by model -- dashboard reads from HERE
CREATE MATERIALIZED VIEW mv_hourly_by_model
ENGINE = SummingMergeTree()
ORDER BY (org_id, hour, routed_model, provider)
AS SELECT
    org_id,
    toStartOfHour(timestamp) AS hour,
    routed_model,
    provider,
    count()                        AS total_requests,
    sum(cost_usd)                  AS total_cost_usd,
    avg(latency_ms)                AS avg_latency_ms,
    quantile(0.95)(latency_ms)     AS p95_latency_ms,
    quantile(0.99)(latency_ms)     AS p99_latency_ms,
    countIf(status = 'error')      AS error_count,
    countIf(cached = 1)            AS cache_hits
FROM request_logs
GROUP BY org_id, hour, routed_model, provider;
```

Similar materialized views exist for team-level aggregation, feature-level aggregation, and daily cost summaries. The dashboard is always fast because it never queries the raw table.

Data auto-expires after 365 days via TTL. You never have to think about cleanup.

---

## The 5ms Overhead Challenge: How to Build a Proxy That Nobody Notices

If your proxy adds 200ms to every LLM call, nobody will use it. Period. LLM responses already take 500ms to 5 seconds. Adding meaningful latency on top of that is a dealbreaker.

TokenMeter's target: **less than 5ms at p99** for the entire pre-forwarding pipeline. Here is how we hit that number:

**1. Everything after forwarding is async.**

The most important architectural decision in the entire system. Cost calculation, usage tracking, budget spend recording, alert delivery -- none of it blocks the response path. The proxy forwards the request, gets the response, enriches it with metadata, and returns it. Usage tracking happens in a background buffer.

```python
# The usage tracker uses a deque buffer + background flush loop
class UsageTracker:
    def __init__(self, buffer_size=100, flush_interval=5.0):
        self._buffer: Deque[UsageRecord] = deque()
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval

    async def track(self, record: UsageRecord):
        """Non-blocking: just append to the buffer."""
        self._buffer.append(record)
        if len(self._buffer) >= self._buffer_size:
            await self._flush()

    async def _flush_loop(self):
        """Background task: flush every 5 seconds."""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            if self._buffer:
                await self._flush()

    async def _flush(self):
        """Batch insert to ClickHouse -- optimized for throughput."""
        records = list(self._buffer)
        self._buffer.clear()
        await self._ch_client.execute(
            "INSERT INTO request_logs (...) VALUES", *rows
        )
```

Records accumulate in memory and flush to ClickHouse every 5 seconds or when 100 records accumulate -- whichever comes first. Batch inserts are what ClickHouse is optimized for. If a flush fails, records are re-added to the buffer (with a 10x cap to prevent OOM).

**2. Classification uses heuristics, not LLMs.**

The request classifier runs regex and keyword matching -- sub-millisecond. I considered calling a small model to classify complexity, but even GPT-4.1-nano adds 100-200ms. That would defeat the entire purpose of the proxy. Regex and keyword sets give us 85-90% accuracy at 0.1ms latency. Worth the trade-off.

**3. Budget checks read from in-memory counters.**

The budget monitor keeps spend counters in a Python dictionary, not in PostgreSQL. Every `record_spend()` call increments an in-memory float. The hard limit check is a dictionary lookup and a comparison -- effectively zero latency. Budget state is periodically synced to PostgreSQL for durability, but the hot path never touches the database.

**4. Connection pooling on the provider side.**

The `httpx.Client` is initialized once at startup with keep-alive connections to each provider. No per-request TCP handshake, no TLS negotiation overhead. The proxy maintains persistent connections to OpenAI, Anthropic, and Google.

**5. Minimal synchronous work in the request path.**

Count the synchronous operations before we forward: validate API key (hash lookup in Redis), check rate limit (Redis INCR), check cache (Redis GET), classify request (regex), pick model (dictionary lookup), check budget (in-memory comparison). Six operations, all sub-millisecond. That is how you stay under 5ms.

---

## Budget Enforcement That Actually Stops the Bleeding

Dashboards are great. But dashboards do not prevent the 3 AM runaway that racks up $2,000 before anyone wakes up.

TokenMeter has **hard budget enforcement** built into the proxy pipeline. Before every request is forwarded to a provider, the budget monitor checks: *"Has this org/team/feature exceeded its spend limit?"* If yes, the request gets a `429 Budget Exceeded` response immediately. No exceptions.

Here is the enforcement logic:

```python
def check_hard_limit(self, org_id, *, team=None, feature=None):
    """Returns the exceeded budget, or None if all clear."""
    for budget in self._budgets.values():
        if budget.org_id != org_id or not budget.enabled or not budget.hard_limit:
            continue
        if budget.team and budget.team != team:
            continue
        if budget.feature and budget.feature != feature:
            continue
        if budget.current_spend_usd >= budget.amount_usd:
            return budget  # BLOCKED
    return None  # All clear

def record_spend(self, org_id, amount_usd, *, team=None, feature=None,
                 model=None, provider=None):
    """Record spend and return any triggered alerts."""
    triggered = []
    for budget in self._budgets.values():
        if budget.org_id != org_id or not budget.enabled:
            continue
        # Check scope filters
        if budget.team and budget.team != team:
            continue

        budget.current_spend_usd += amount_usd
        utilization = budget.current_spend_usd / budget.amount_usd * 100

        # Check each threshold
        for threshold in budget.thresholds:
            if threshold.notified:
                continue
            if utilization >= threshold.percentage:
                alert = BudgetAlert(
                    budget_id=budget.id,
                    severity=threshold.severity,
                    current_spend_usd=budget.current_spend_usd,
                    message=f"Budget '{budget.name}' at {utilization:.1f}%"
                )
                threshold.notified = True
                triggered.append(alert)
    return triggered
```

You configure budgets at multiple levels:

- **Organization-wide**: "Do not spend more than $5,000/month total"
- **Per-team**: "The search team gets $2,000/month"
- **Per-feature**: "Autocomplete is capped at $500/month"
- **Per-model**: "GPT-5.2 usage cannot exceed $1,000/month"

Each budget supports **multiple thresholds** with different actions:

```
Budget Alert: Search Team monthly spend has reached 80%
   Spent: $1,600.00 / $2,000.00
   Severity: WARNING
   Channel: #ai-costs
```

At 50%, maybe you get a Slack message. At 80%, a warning email. At 100%, requests start getting blocked. Alerts fire in real time -- not on a cron job, not with a 15-minute delay. Every single request runs through the check. This is why budget enforcement is in the proxy pipeline, not a separate service.

---

## Mistakes I Made (So You Don't Have To)

Building TokenMeter was not a straight line. Here are the mistakes that cost me the most time:

**Mistake 1: In-memory stores without durability.**

The first version kept all budget state and usage counters purely in memory. It was fast -- sub-microsecond lookups. But when the proxy restarted (deployment, crash, scaling event), all budget state reset to zero. A team at 95% of their budget limit would suddenly show 0% after a deploy. The fix was simple but important: persist budget state to PostgreSQL on every threshold crossing and on a 60-second sync interval, and reload state on startup. The hot path still reads from memory, but durability comes from the periodic sync.

**Mistake 2: Streaming token counts are approximate.**

When you proxy a streaming response, you do not get a final `usage` object until the stream ends (and some providers never send one). My initial approach was to count SSE chunks as tokens: one chunk equals roughly one token. This is approximately correct -- most providers send one token per chunk -- but not exactly. OpenAI's newer models sometimes batch 2-3 tokens per chunk, and the first chunk often contains the role metadata, not a content token. The current approach: use the provider-reported `usage` object from the final chunk if available; fall back to chunk counting only when the provider does not report usage.

```python
# Use provider-reported usage if available, otherwise estimate
if final_usage:
    usage = final_usage
else:
    usage = UsageInfo(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
```

**Mistake 3: Not handling ClickHouse flush failures gracefully.**

The first version dropped records silently when a ClickHouse flush failed. In production, ClickHouse Cloud occasionally has network blips lasting 1-2 seconds. That means 5-10 requests with zero cost tracking -- which, if those requests include expensive GPT-5 calls, means real money disappearing from your dashboard. The fix: on flush failure, re-add records to the buffer (with a cap at 10x buffer size to prevent OOM), and retry on the next flush cycle.

```python
except Exception as e:
    logger.error("Failed to flush to ClickHouse: %s -- records lost: %d", e, len(records))
    # Re-add records to buffer for retry (limited to avoid OOM)
    if len(self._buffer) < self._buffer_size * 10:
        self._buffer.extend(records)
```

**Mistake 4: Trying to monkey-patch the OpenAI SDK.**

My first SDK prototype monkey-patched the official OpenAI client at import time -- intercept `httpx` calls, inject headers, done. It worked for exactly one OpenAI SDK version. The next minor release changed internal method signatures and the whole thing broke silently. The fix: build a standalone client that speaks the same API but controls its own HTTP transport. More code upfront, but it survives SDK updates without breaking.

**Mistake 5: Not partitioning ClickHouse by month from day one.**

I started with a flat MergeTree table. At 500K rows, queries were fast. At 5M rows, even with materialized views, some ad-hoc queries on raw data were slow because ClickHouse was scanning partitions it did not need. Adding `PARTITION BY toYYYYMM(timestamp)` and an appropriate `ORDER BY (org_id, timestamp, id)` was a one-line fix but required a full table rebuild. Do it from the start.

---

## By the Numbers

Engineers want specifics, not hand-waving. Here is what TokenMeter delivers:

| Metric | Value |
|---|---|
| **Proxy overhead** | <5ms per request (p99) |
| **Smart routing savings** | Up to 60% on mixed workloads |
| **Classification accuracy** | ~87% agreement with human labels on complexity |
| **Classification latency** | <0.5ms (regex + keyword heuristics) |
| **ClickHouse query time** | 22-61ms on 3M rows (via materialized views) |
| **Buffer flush interval** | 5 seconds or 100 records (whichever first) |
| **Buffer retry on failure** | Yes, up to 10x buffer size cap |
| **Supported providers** | 3 (OpenAI, Anthropic, Google) |
| **Supported models** | 15+ across all providers |
| **Streaming support** | Full SSE pass-through with async token counting |
| **Budget check latency** | <0.1ms (in-memory dictionary lookup) |
| **Data retention** | 365 days (TTL auto-expiry) |
| **Infrastructure cost** | ~$50-80/month (Fly.io + Supabase + ClickHouse Cloud + Upstash) |
| **SDK languages** | Python (PyPI) + Node.js (npm) |
| **Integration time** | One import change, <5 minutes |

The 60% savings number comes from real workload analysis. Most production applications have a **long tail of simple requests** -- classification, extraction, translation, formatting -- that do not need frontier models. When 70% of your traffic is simple and you route it to models that cost 10-120x less, the math works out fast.

Here is a concrete example. Suppose your application makes 10,000 LLM requests per day with this distribution:

- **7,000 simple** (translation, extraction, classification): originally `gpt-4.1` at $2.00/M tokens
- **2,000 medium** (summarization, Q&A with context): originally `gpt-4.1` at $2.00/M tokens
- **1,000 complex** (code generation, multi-step reasoning): stays on `gpt-4.1` at $2.00/M tokens

Average 500 tokens per request. Without routing, everything goes to `gpt-4.1`: **$10.00/day**.

With smart routing:
- 7,000 simple requests --> `gpt-4.1-nano` at $0.10/M: **$0.35/day**
- 2,000 medium requests --> `gpt-4.1-mini` at $0.40/M: **$0.40/day**
- 1,000 complex requests --> `gpt-4.1` at $2.00/M: **$1.00/day**

Total: **$1.75/day** vs $10.00/day. That is an **82.5% reduction** -- $247.50 saved per month. On 100,000 requests per day, that scales to $2,475/month saved.

The infrastructure cost surprised me too. Fly.io for the proxy (~$15/month), Supabase for PostgreSQL (free tier or $25/month), ClickHouse Cloud ($20-30/month for moderate usage), Upstash Redis (free tier). **The proxy pays for itself in the first week** for any team spending more than $200/month on LLMs.

---

## Architecture: Why These Tools, Why These Trade-offs

**Why Fly.io over Cloud Run?** Cloud Run scales to zero, which sounds great until you realize it means cold starts. A proxy needs to be *always on* -- persistent connections, warm caches, in-memory buffers that survive between requests. Fly.io gives me lightweight VMs that stay running, with global edge deployment so the proxy is close to both the client and the LLM provider. Cold starts are a luxury a proxy cannot afford.

**Why FastAPI?** The proxy is I/O-bound, not CPU-bound. Async Python with FastAPI handles thousands of concurrent connections efficiently. The overhead of Python versus Go or Rust is irrelevant here because 99% of the wall-clock time is spent waiting for the upstream LLM provider. The pre-forwarding pipeline (auth, classify, route, budget check) runs in <5ms regardless of language. FastAPI's ecosystem -- Pydantic for request validation, Starlette for SSE streaming -- saved weeks of development time.

**Why the SDK wraps instead of monkey-patching.** I considered monkey-patching the OpenAI SDK at import time -- intercept `httpx` calls, inject headers, done. But monkey-patching breaks in unpredictable ways across SDK versions. TokenMeter's SDK builds a standalone client with the same `client.chat.completions.create()` interface, using its own `httpx.Client` pointed at the proxy. When OpenAI ships a new SDK version, we do not break. That is worth the extra engineering effort.

**Why heuristic classification instead of a small LLM.** Calling even the cheapest model to classify complexity would add 100-200ms of latency to every request. The heuristic classifier runs in <0.5ms with ~87% accuracy. For the 13% it gets wrong, the consequence is that a medium-complexity request gets routed to a cheap model and produces a slightly worse response, or a simple request gets routed to an expensive model and wastes a fraction of a cent. The latency trade-off is not worth it.

---

## What's Next

TokenMeter solves the "where is the money going?" problem today. But there is a lot more to build:

**Semantic caching** -- Right now, caching is exact-match on the request body. Semantic caching would recognize that "What's the capital of France?" and "Tell me the capital city of France" should return the same cached response. This alone could cut costs another 20-30% for applications with repetitive query patterns.

**Cost anomaly detection** -- Instead of just fixed budget thresholds, use statistical methods to detect *unusual* spending patterns. "The search team's spend is 3x higher than the same day last week" is a more useful signal than "you hit 80% of an arbitrary cap."

**Team-level cost allocation reports** -- Finance teams want to charge AI costs back to the teams that incur them. TokenMeter already has the per-team data; the next step is exportable reports, integrations with billing systems, and showback/chargeback workflows.

**More providers** -- Mistral, Cohere, AWS Bedrock, Azure OpenAI. The proxy architecture makes this straightforward -- each provider is an adapter that translates between OpenAI-compatible format and the provider's native API. The routing engine already handles provider-agnostic model selection.

**Adaptive routing** -- Instead of static complexity thresholds, learn from historical data. If a particular feature consistently produces good results with `gpt-4.1-nano`, lower its routing threshold automatically. If another feature has high error rates on cheap models, promote it to a higher tier.

---

## Try It

If you are spending money on LLMs and cannot answer "which feature costs the most?" -- that is exactly the problem TokenMeter was built to solve.

```bash
# Python
pip install tokenmeter

# Node.js
npm install tokenmeter
```

Then change one import:

```python
# Before
from openai import OpenAI

# After
from tokenmeter import OpenAI

client = OpenAI()  # Everything else stays the same
```

Open the dashboard and finally understand where your AI budget goes.

The repo is open source (MIT). **Star it on [GitHub](https://github.com/nirbhaysingh1/tokenmeter)** if LLM cost visibility resonates with you.

And if you have your own LLM cost horror story -- that $10,000 invoice nobody can explain, that runaway loop that burned through your credits overnight, that model upgrade that silently 5x'd your costs -- **I would love to hear it.** Drop a comment or connect with me on [LinkedIn](https://www.linkedin.com/in/nirbhaysingh1/). Every horror story makes the case for better tooling.

---

*TokenMeter is open source under the MIT license. Built with FastAPI, Next.js, ClickHouse, PostgreSQL, and a healthy frustration with opaque AI billing. The entire codebase -- proxy, SDKs, dashboard, database schemas -- is on [GitHub](https://github.com/nirbhaysingh1/tokenmeter).*

**About the Author:** DevOps and MLOps engineer passionate about cloud cost optimization and open source. Connect on [LinkedIn](https://www.linkedin.com/in/nirbhaysingh1/).