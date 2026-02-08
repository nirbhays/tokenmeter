-- ============================================================================
-- TokenMeter — Seed Data
-- ============================================================================

-- Insert a demo organization
INSERT INTO organizations (id, name, slug, plan) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Demo Organization', 'demo', 'pro');

-- Insert a demo user
INSERT INTO users (id, email, name, clerk_user_id) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'demo@tokenmeter.dev', 'Demo User', 'user_demo');

-- Link user to org
INSERT INTO org_memberships (org_id, user_id, role) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'owner');

-- Insert demo API key (hash of "tm_demo_key_for_testing")
INSERT INTO api_keys (org_id, name, key_hash, key_prefix, scopes) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Demo Key', 
     'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'tm_demo', 
     ARRAY['proxy', 'dashboard', 'admin']);

-- Insert default routing config
INSERT INTO routing_configs (org_id, mode, enabled) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'cost-optimized', true);

-- Insert sample budget
INSERT INTO budgets (org_id, name, amount_usd, period, thresholds) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Monthly AI Spend', 500.00, 'monthly',
     '[{"percentage": 50, "severity": "info", "channels": ["slack"]},
       {"percentage": 80, "severity": "warning", "channels": ["slack", "email"]},
       {"percentage": 100, "severity": "critical", "channels": ["slack", "email", "webhook"]}]');

-- Insert subscription
INSERT INTO subscriptions (org_id, plan, status, monthly_request_limit, monthly_token_limit, max_api_keys, max_team_members, features) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'pro', 'active', 500000, 50000000, 20, 20,
     ARRAY['advanced_dashboard', 'cost_tracking', 'smart_routing', 'budget_alerts', 'team_management', 'slack_integration']);
