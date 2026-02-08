# ============================================================================
# TokenMeter — Terraform Infrastructure
# ============================================================================

terraform {
  required_version = ">= 1.5"

  required_providers {
    fly = {
      source  = "fly-apps/fly"
      version = "~> 0.1"
    }
  }

  backend "s3" {
    bucket = "tokenmeter-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
}

# ── Locals ────────────────────────────────────────────────────────────────────

locals {
  project     = "tokenmeter"
  environment = var.environment
  region      = var.region
  tags = {
    Project     = local.project
    Environment = local.environment
    ManagedBy   = "terraform"
  }
}
