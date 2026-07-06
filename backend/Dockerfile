# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy only dependency files first for better caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

# ---- Stage 2: Runtime ----
FROM python:3.11-slim AS runtime

LABEL maintainer="swap-mitra"
LABEL description="Live DDoS Map — FastAPI backend"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Create data directory (can be overridden by a volume mount)
RUN mkdir -p /data

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app /data
USER appuser

# Default env vars (override in production)
ENV DDOS_DB_PATH=/data/events.db \
    MAXMIND_DB_PATH=/data/GeoLite2-City.mmdb \
    ENABLE_SCHEDULER=true \
    LOG_LEVEL=INFO \
    PORT=8000

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
