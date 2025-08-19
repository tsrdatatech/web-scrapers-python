# Multi-stage Docker build for production-ready web scraper
FROM python:3.12-slim AS builder

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.6.1

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy dependency files
WORKDIR /app
COPY pyproject.toml poetry.lock README.md ./
COPY src/ ./src/

# Install dependencies
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python:3.12-slim AS production

# Install runtime dependencies including Playwright browsers
RUN apt-get update && apt-get install -y \
    # Required for Playwright
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    # Additional utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r scraper && useradd -r -g scraper scraper

# Set up application directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=scraper:scraper /app/.venv /app/.venv

# Copy application code
COPY --chown=scraper:scraper . .

# Make sure to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Create directories for data persistence
RUN mkdir -p /app/storage /app/logs && \
    chown -R scraper:scraper /app/storage /app/logs

# Switch to non-root user
USER scraper

# Set default command
CMD ["python", "-m", "src.main", "--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import sys; from src.core.logger import get_logger; get_logger('health'); sys.exit(0)" || exit 1

# Labels for metadata
LABEL maintainer="Portfolio Project" \
      description="Universal Web Scraper - Production Docker Image" \
      version="1.0.0" \
      org.opencontainers.image.source="https://github.com/tsrdatatech/web-scrapers-python"