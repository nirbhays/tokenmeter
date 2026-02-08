-- ============================================================================
-- TokenMeter — ClickHouse Schema
-- Time-series request logs and materialized views for fast aggregation.
-- ============================================================================

-- ── Main request log table ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS request_logs (
    id                      String,
    timestamp               DateTime64(3, 'UTC'),
    org_id                  String,
    team                    String DEFAULT '',
    feature                 String DEFAULT '',
    api_key_id              String,

    -- Request details
    requested_model         String,
    routed_model            String,
    provider                String,
    endpoint                String,
    stream                  UInt8 DEFAULT 0,

    -- Tokens
    prompt_tokens           UInt32 DEFAULT 0,
    completion_tokens       UInt32 DEFAULT 0,
    total_tokens            UInt32 DEFAULT 0,

    -- Cost
    cost_usd                Float64 DEFAULT 0,
    input_cost_usd          Float64 DEFAULT 0,
    output_cost_usd         Float64 DEFAULT 0,

    -- Performance
    latency_ms              Float64 DEFAULT 0,
    time_to_first_token_ms  Float64 DEFAULT 0,

    -- Status
    status                  String DEFAULT 'success',
    status_code             UInt16 DEFAULT 200,
    error_message           String DEFAULT '',

    -- Routing
    routing_mode            String DEFAULT '',
    complexity_score        Float32 DEFAULT 0,
    cached                  UInt8 DEFAULT 0
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (org_id, timestamp, id)
TTL timestamp + INTERVAL 365 DAY
SETTINGS index_granularity = 8192;


-- ── Materialized View: Hourly aggregation by org + model ─────────────────────

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_by_model
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (org_id, hour, routed_model, provider)
AS SELECT
    org_id,
    toStartOfHour(timestamp) AS hour,
    routed_model,
    provider,
    count()                 AS total_requests,
    sum(prompt_tokens)      AS total_prompt_tokens,
    sum(completion_tokens)  AS total_completion_tokens,
    sum(total_tokens)       AS total_tokens,
    sum(cost_usd)           AS total_cost_usd,
    avg(latency_ms)         AS avg_latency_ms,
    quantile(0.50)(latency_ms)  AS p50_latency_ms,
    quantile(0.95)(latency_ms)  AS p95_latency_ms,
    quantile(0.99)(latency_ms)  AS p99_latency_ms,
    countIf(status = 'error')   AS error_count,
    countIf(cached = 1)         AS cache_hits
FROM request_logs
GROUP BY org_id, hour, routed_model, provider;


-- ── Materialized View: Hourly aggregation by org + team ──────────────────────

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_by_team
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (org_id, hour, team)
AS SELECT
    org_id,
    toStartOfHour(timestamp) AS hour,
    team,
    count()                 AS total_requests,
    sum(total_tokens)       AS total_tokens,
    sum(cost_usd)           AS total_cost_usd,
    avg(latency_ms)         AS avg_latency_ms
FROM request_logs
WHERE team != ''
GROUP BY org_id, hour, team;


-- ── Materialized View: Hourly aggregation by org + feature ───────────────────

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_by_feature
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (org_id, hour, feature)
AS SELECT
    org_id,
    toStartOfHour(timestamp) AS hour,
    feature,
    count()                 AS total_requests,
    sum(total_tokens)       AS total_tokens,
    sum(cost_usd)           AS total_cost_usd,
    avg(latency_ms)         AS avg_latency_ms
FROM request_logs
WHERE feature != ''
GROUP BY org_id, hour, feature;


-- ── Materialized View: Daily cost summary ────────────────────────────────────

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_cost
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (org_id, day)
AS SELECT
    org_id,
    toDate(timestamp) AS day,
    count()                 AS total_requests,
    sum(total_tokens)       AS total_tokens,
    sum(cost_usd)           AS total_cost_usd,
    sum(input_cost_usd)     AS total_input_cost_usd,
    sum(output_cost_usd)    AS total_output_cost_usd
FROM request_logs
GROUP BY org_id, day;
