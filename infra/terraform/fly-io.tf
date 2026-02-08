# ── Fly.io Application ────────────────────────────────────────────────────────

resource "fly_app" "tokenmeter_api" {
  name = "tokenmeter-api-${var.environment}"
  org  = "personal"
}

resource "fly_machine" "tokenmeter_api" {
  app    = fly_app.tokenmeter_api.name
  region = var.region
  name   = "tokenmeter-api-1"

  image = "registry.fly.io/tokenmeter-api-${var.environment}:latest"

  cpus     = 2
  memory   = 1024
  cpu_kind = "shared"

  env = {
    ENVIRONMENT        = var.environment
    DATABASE_URL       = var.database_url
    REDIS_URL          = var.redis_url
    CLICKHOUSE_HOST    = var.clickhouse_host
    CLICKHOUSE_PASSWORD = var.clickhouse_password
    OPENAI_API_KEY     = var.openai_api_key
    ANTHROPIC_API_KEY  = var.anthropic_api_key
    GOOGLE_API_KEY     = var.google_api_key
    STRIPE_SECRET_KEY  = var.stripe_secret_key
    CLERK_SECRET_KEY   = var.clerk_secret_key
    SLACK_WEBHOOK_URL  = var.slack_webhook_url
  }

  services = [
    {
      ports = [
        {
          port     = 443
          handlers = ["tls", "http"]
        },
        {
          port     = 80
          handlers = ["http"]
        }
      ]
      protocol      = "tcp"
      internal_port = 8000
    }
  ]
}
