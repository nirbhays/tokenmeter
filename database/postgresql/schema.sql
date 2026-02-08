-- ============================================================================
-- TokenMeter — PostgreSQL Schema
-- Stores users, organizations, API keys, routing rules, budgets, subscriptions.
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Organizations ────────────────────────────────────────────────────────────

CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    clerk_org_id    VARCHAR(255) UNIQUE,
    plan            VARCHAR(50) NOT NULL DEFAULT 'free',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    settings        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_org_slug ON organizations(slug);
CREATE INDEX idx_org_clerk ON organizations(clerk_org_id);

-- ── Users ────────────────────────────────────────────────────────────────────

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(320) UNIQUE NOT NULL,
    name            VARCHAR(255),
    clerk_user_id   VARCHAR(255) UNIQUE NOT NULL,
    avatar_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_clerk ON users(clerk_user_id);

-- ── Organization Memberships ─────────────────────────────────────────────────

CREATE TABLE org_memberships (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(50) NOT NULL DEFAULT 'member', -- owner, admin, member
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (org_id, user_id)
);

-- ── API Keys ─────────────────────────────────────────────────────────────────

CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL DEFAULT 'default',
    key_hash        VARCHAR(128) NOT NULL UNIQUE,
    key_prefix      VARCHAR(20) NOT NULL, -- e.g., "tm_abc..."
    scopes          TEXT[] DEFAULT ARRAY['proxy', 'dashboard'],
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    revoked         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID REFERENCES users(id)
);

CREATE INDEX idx_apikey_org ON api_keys(org_id);
CREATE INDEX idx_apikey_hash ON api_keys(key_hash);

-- ── Provider Credentials ─────────────────────────────────────────────────────

CREATE TABLE provider_credentials (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider        VARCHAR(50) NOT NULL, -- openai, anthropic, google
    api_key_encrypted BYTEA NOT NULL, -- encrypted with pgcrypto
    label           VARCHAR(255),
    is_default      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (org_id, provider, label)
);

-- ── Routing Rules ────────────────────────────────────────────────────────────

CREATE TABLE routing_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    priority        INTEGER NOT NULL DEFAULT 0,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    source_models   TEXT[] DEFAULT '{}',
    complexity_levels TEXT[] DEFAULT '{}',
    teams           TEXT[] DEFAULT '{}',
    features        TEXT[] DEFAULT '{}',
    max_tokens_threshold INTEGER,
    min_tokens_threshold INTEGER,
    target_model    VARCHAR(100) NOT NULL,
    target_provider VARCHAR(50),
    fallback_model  VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_routing_org ON routing_rules(org_id, priority DESC);

-- ── Routing Config ───────────────────────────────────────────────────────────

CREATE TABLE routing_configs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id          UUID UNIQUE NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    mode            VARCHAR(50) NOT NULL DEFAULT 'cost-optimized',
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    model_aliases   JSONB DEFAULT '{}',
    fallback_models JSONB DEFAULT '{}',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Budgets ──────────────────────────────────────────────────────────────────

CREATE TABLE budgets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    team            VARCHAR(100),
    feature         VARCHAR(100),
    model           VARCHAR(100),
    provider        VARCHAR(50),
    amount_usd      DECIMAL(12, 4) NOT NULL,
    period          VARCHAR(20) NOT NULL DEFAULT 'monthly',
    thresholds      JSONB DEFAULT '[]',
    hard_limit      BOOLEAN NOT NULL DEFAULT FALSE,
    current_spend_usd DECIMAL(12, 6) DEFAULT 0,
    period_start    TIMESTAMPTZ DEFAULT NOW(),
    period_end      TIMESTAMPTZ,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_budget_org ON budgets(org_id);

-- ── Budget Alerts ────────────────────────────────────────────────────────────

CREATE TABLE budget_alerts (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    budget_id           UUID NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    threshold_percentage DECIMAL(5, 2) NOT NULL,
    severity            VARCHAR(20) NOT NULL,
    current_spend_usd   DECIMAL(12, 6) NOT NULL,
    budget_amount_usd   DECIMAL(12, 4) NOT NULL,
    utilization_pct     DECIMAL(5, 1) NOT NULL,
    message             TEXT,
    channels_notified   TEXT[],
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alert_budget ON budget_alerts(budget_id, created_at DESC);
CREATE INDEX idx_alert_org ON budget_alerts(org_id, created_at DESC);

-- ── Subscriptions (Stripe) ───────────────────────────────────────────────────

CREATE TABLE subscriptions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id                  UUID UNIQUE NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    plan                    VARCHAR(50) NOT NULL DEFAULT 'free',
    stripe_subscription_id  VARCHAR(255),
    status                  VARCHAR(50) NOT NULL DEFAULT 'active',
    current_period_start    TIMESTAMPTZ,
    current_period_end      TIMESTAMPTZ,
    monthly_request_limit   INTEGER DEFAULT 10000,
    monthly_token_limit     BIGINT DEFAULT 1000000,
    max_api_keys            INTEGER DEFAULT 2,
    max_team_members        INTEGER DEFAULT 3,
    features                TEXT[] DEFAULT ARRAY['basic_dashboard', 'cost_tracking'],
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Webhook Endpoints ────────────────────────────────────────────────────────

CREATE TABLE webhook_endpoints (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    secret          VARCHAR(255) NOT NULL,
    events          TEXT[] DEFAULT ARRAY['budget_alert'],
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Updated-at trigger ───────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_org_updated BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_user_updated BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_routing_updated BEFORE UPDATE ON routing_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_budget_updated BEFORE UPDATE ON budgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_sub_updated BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
