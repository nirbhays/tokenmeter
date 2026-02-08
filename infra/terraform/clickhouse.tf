# ── ClickHouse Cloud ──────────────────────────────────────────────────────────
# Note: ClickHouse Cloud is provisioned via their dashboard or API.
# This file documents the expected configuration.

# In production, use ClickHouse Cloud managed service:
# https://clickhouse.cloud
#
# Required configuration:
#   - Service: tokenmeter-analytics
#   - Region: us-east-1 (or closest to your Fly.io region)
#   - Tier: Development (scale as needed)
#   - Database: tokenmeter
#   - Apply schema from: database/clickhouse/schema.sql
