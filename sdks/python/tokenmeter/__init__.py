"""
TokenMeter Python SDK — Drop-in replacement for the OpenAI Python client.

Usage:
    # Before:
    from openai import OpenAI

    # After (one-line change):
    from tokenmeter import OpenAI

    client = OpenAI()  # Uses TOKENMETER_API_KEY and TOKENMETER_BASE_URL env vars
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    # response includes cost tracking: response.tm_cost_usd, response.tm_latency_ms
"""

from tokenmeter.client import TokenMeterClient as OpenAI

__version__ = "0.1.0"
__all__ = ["OpenAI", "__version__"]
