# Multi-stage Dockerfile for MCP Servers
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY docker/mcp_server_entrypoint.py ./

# Create necessary directories
RUN mkdir -p /app/output /app/temp /app/logs

# Expose port (will be overridden by environment)
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the MCP server
CMD ["python", "mcp_server_entrypoint.py"]
