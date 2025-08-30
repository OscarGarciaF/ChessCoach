# Multi-stage Docker build for the Interesting Chess data scraper
# Optimized for AWS Batch deployment

FROM python:3.11-slim as builder

# Set build-time metadata
LABEL maintainer="Chess Coach Team"
LABEL description="Chess.com data scraper for finding interesting win streaks"
LABEL version="1.0.0"

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set up the application directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Copy environment variables from builder
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create the same non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set up application directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Create output directory with proper permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# Switch to non-root user
USER appuser

# Set default environment variables for the application
ENV IC_OUTPUT_DIR=/app/data \
    IC_SLEEP_SECONDS=0.25 \
    IC_DEFAULT_DAYS=30

# Health check to ensure the application is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; import requests; sys.exit(0)"

# Default command - can be overridden in AWS Batch job definition
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]

# Add labels for better container management
LABEL org.opencontainers.image.title="Interesting Chess Scraper"
LABEL org.opencontainers.image.description="Scrapes Chess.com for interesting win streaks"
LABEL org.opencontainers.image.vendor="Chess Coach Team"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/YourRepo/ChessCoach"
