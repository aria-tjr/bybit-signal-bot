FROM python:3.11-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    libpq-dev \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Skip TA-Lib native installation since we'll use pandas-ta as alternative

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for enhanced features
RUN pip install --no-cache-dir uvloop asyncio

# Copy application code
COPY app/ ./app/
COPY .env ./

# Create necessary directories
RUN mkdir -p /app/models /app/logs

# Copy trading test scripts for Docker environment
COPY test_trading_connection.py ./
COPY signal_integration_example.py ./

# Create non-root user
RUN useradd -m -s /bin/bash botuser && \
    chown -R botuser:botuser /app

USER botuser

# Environment variables for enhanced bot
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expose ports
EXPOSE 8000
EXPOSE 8001

# Health check for the enhanced bot
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run the main application
CMD ["python", "-m", "app.main"] 