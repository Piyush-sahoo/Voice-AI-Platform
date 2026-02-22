FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc curl libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install uv
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Copy shared modules
COPY shared ./shared

# Copy for backwards compatibility
COPY shared/database ./database
COPY shared/auth ./auth

# Copy all services
COPY services ./services

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run analytics service
CMD ["uvicorn", "services.analytics.main:app", "--host", "0.0.0.0", "--port", "8001"]
