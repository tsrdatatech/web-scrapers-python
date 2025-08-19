# Use Apify's Python Playwright image which includes all browser dependencies
FROM apify/actor-python-playwright:3.12

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install additional Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY *.py ./

# Expose port (if needed for web interface)
EXPOSE 8000

# Default command (using the same pattern as Apify's base image)
CMD ["python3", "-m", "src.main"]
