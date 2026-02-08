"""
Security utilities — API key hashing, generation, webhook signature verification.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Optional


# ── API Key Generation ────────────────────────────────────────────────────────

API_KEY_PREFIX = "tm_"
API_KEY_LENGTH = 48  # total length including prefix


def generate_api_key() -> str:
    """Generate a new TokenMeter API key with the tm_ prefix."""
    random_part = secrets.token_urlsafe(36)[:API_KEY_LENGTH - len(API_KEY_PREFIX)]
    return f"{API_KEY_PREFIX}{random_part}"


def hash_api_key(key: str, algorithm: str = "sha256") -> str:
    """Hash an API key for storage.  Never store raw keys."""
    return hashlib.new(algorithm, key.encode("utf-8")).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str, algorithm: str = "sha256") -> bool:
    """Constant-time comparison of a plain key against its hash."""
    computed = hashlib.new(algorithm, plain_key.encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed, hashed_key)


def mask_api_key(key: str) -> str:
    """Return a masked version of the key for display: tm_abc...xyz"""
    if len(key) <= 10:
        return key[:3] + "***"
    return key[:6] + "..." + key[-4:]


# ── Webhook Signatures ───────────────────────────────────────────────────────

def compute_webhook_signature(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for a webhook payload."""
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    *,
    max_age_seconds: Optional[int] = 300,
    timestamp: Optional[int] = None,
) -> bool:
    """Verify a webhook signature.  Optionally check timestamp freshness."""
    expected = compute_webhook_signature(payload, secret)
    sig_valid = hmac.compare_digest(expected, signature)

    if not sig_valid:
        return False

    if max_age_seconds and timestamp:
        age = abs(time.time() - timestamp)
        if age > max_age_seconds:
            return False

    return True
