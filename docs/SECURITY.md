# Security

## Threat Model

TokenMeter acts as a proxy between your application and LLM providers. This means **all request and response data flows through TokenMeter**. We take this responsibility seriously.

## API Key Security

- **Keys are hashed** using SHA-256 before storage. Raw keys are never persisted.
- **Keys use the `tm_` prefix** for easy identification in logs and leak detection.
- **Key masking**: Only the first 6 and last 4 characters are shown in the UI (`tm_abc...xyz`).
- **Constant-time comparison** for key validation (prevents timing attacks).

## Data at Rest

### What We Store

| Data | Storage | Retention |
|---|---|---|
| Token counts, cost, latency | ClickHouse | 365 days (configurable) |
| Model, provider, team, feature | ClickHouse | 365 days |
| Request/response bodies | **NOT stored** by default | — |
| API keys (hashed) | PostgreSQL | Until revoked |
| User info | PostgreSQL | Until account deletion |

### Zero-Logging Mode

Enterprise customers can enable `ZERO_LOGGING_MODE=true`, which:
- Does **not** store request/response content
- Does **not** log message bodies
- Only records: token counts, cost, latency, model, provider, status code
- Metadata tags (team, feature) are still logged

## Data in Transit

- All external communication uses TLS 1.3
- Fly.io provides automatic TLS termination
- Provider API calls use HTTPS

## Provider Credentials

- LLM provider API keys are stored as environment variables / Fly.io secrets
- Per-org provider keys (when configured) are encrypted with pgcrypto in PostgreSQL
- Keys are never exposed through the dashboard API

## Webhook Security

- Outbound webhooks include HMAC-SHA256 signatures
- Signature format: `sha256=<hex_digest>`
- Recipients should verify signatures before processing

## Rate Limiting

- Redis-backed sliding window rate limiter
- Configurable per-org limits
- Prevents abuse and runaway costs

## Vulnerability Disclosure

If you discover a security vulnerability, please email security@tokenmeter.dev. Do not open a public issue.

## Compliance Considerations

- **SOC 2**: Architecture supports SOC 2 compliance (audit logging, access controls)
- **GDPR**: Zero-logging mode supports GDPR requirements for data minimization
- **Data Residency**: Deployable to any Fly.io region for data residency requirements
