# Changelog

All notable changes to TokenMeter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-08

### Added

- 🎉 **Initial release**
- OpenAI-compatible proxy with streaming SSE support
- Smart routing engine with complexity-based classification
  - Cost-optimized routing: sends simple queries to cheap models (GPT-4.1-nano)
  - Latency-optimized routing: sends to fastest available models
  - Quality-optimized routing: sends to best models for complex tasks
- Real-time cost tracking for every API call
- Support for 13 models across 3 providers:
  - **OpenAI**: GPT-5.2, GPT-5, GPT-5-mini, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, o3, o4-mini
  - **Anthropic**: Claude Opus 4, Claude Sonnet 4.5, Claude Haiku 3.5
  - **Google**: Gemini 2.5 Pro, Gemini 2.5 Flash
- Budget management with multi-threshold alerts (Slack, webhook, email)
- Dashboard with real-time spend visualization
  - Cost trend charts
  - Per-model cost breakdown
  - Per-team and per-feature attribution
  - Provider health monitoring
- Response caching with Redis
- Rate limiting
- API key management
- Drop-in Python SDK (`from tokenmeter import OpenAI`)
- Drop-in Node.js SDK (`import OpenAI from 'tokenmeter'`)
- PostgreSQL schema for org/user/key/budget management
- ClickHouse schema for time-series metrics with materialized views
- Docker Compose for local development
- Fly.io deployment configuration
- GitHub Actions CI/CD pipelines
- Comprehensive documentation
