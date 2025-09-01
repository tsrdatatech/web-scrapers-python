# Use Apify's Python Playwright image which includes all browser dependencies
FROM apify/actor-python-playwright:3.12

# Set working directory
WORKDIR /usr/src/app

# Install uv for fast dependency installation
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY *.py ./

# Install dependencies with uv (using pyproject.toml)
RUN uv pip install --system -e .

# Install additional development dependencies that are in pixi but needed for runtime
RUN uv pip install --system \
    crawlee>=0.6.12,<0.7.0 \
    playwright>=1.47.0,<2.0.0 \
    pydantic>=2.0.0,<3.0.0 \
    newspaper3k>=0.2.8 \
    trafilatura>=1.9.0 \
    loguru>=0.7.0 \
    python-dotenv>=1.0.0 \
    httpx>=0.25.0 \
    aiofiles>=23.0.0 \
    structlog>=23.2.0

# Expose port (if needed for web interface)
EXPOSE 8000

# Default command
CMD ["python", "-m", "src.main"]
