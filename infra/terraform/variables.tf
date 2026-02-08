variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "region" {
  description = "Primary deployment region"
  type        = string
  default     = "iad"  # Fly.io IAD (Ashburn, VA)
}

variable "fly_api_token" {
  description = "Fly.io API token"
  type        = string
  sensitive   = true
}

variable "database_url" {
  description = "PostgreSQL connection string"
  type        = string
  sensitive   = true
}

variable "redis_url" {
  description = "Redis connection string"
  type        = string
  sensitive   = true
}

variable "clickhouse_host" {
  description = "ClickHouse Cloud host"
  type        = string
}

variable "clickhouse_password" {
  description = "ClickHouse password"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_api_key" {
  description = "Google API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "stripe_secret_key" {
  description = "Stripe secret key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "clerk_secret_key" {
  description = "Clerk secret key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  default     = ""
}
