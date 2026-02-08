# =============================================================================
# TokenMeter Backend — Production Docker Image
# =============================================================================
# Multi-stage build for minimal image size.
# Based on python:3.12-slim for security (no unnecessary packages).

# Stage 1: Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies needed for compiling Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.12-slim

# Security: run as non-root user
RUN adduser --disabled-password --gecos "" appuser

# Install runtime dependencies only (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY . .

RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Fly.io uses PORT env var; default to 8000 for local dev
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]
