# Use Apify's Python Playwright image which includes all browser dependencies
FROM apify/actor-python-playwright:3.12

# Set working directory
WORKDIR /usr/src/app

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:$PATH"

# Copy pixi configuration files
COPY pixi.toml pixi.lock ./

# Install dependencies using pixi
RUN pixi install --frozen

# Copy source code
COPY src/ ./src/
COPY *.py ./

# Expose port (if needed for web interface)
EXPOSE 8000

# Default command (using pixi environment)
CMD ["pixi", "run", "python", "-m", "src.main"]
