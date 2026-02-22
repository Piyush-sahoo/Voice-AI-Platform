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

# Copy for backwards compatibility (old imports like 'from database.models')
COPY shared/database ./database
COPY shared/auth ./auth

# Copy services (needed for imports)
COPY services ./services

# Create logs directory
RUN mkdir -p /app/logs

# Expose no ports - agent connects outbound to LiveKit

# Health check via process
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "run_agent" || exit 1

# Run agent
CMD ["python", "services/agent/run_agent.py", "start"]
