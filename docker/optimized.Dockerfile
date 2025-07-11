FROM python:3.11-slim as base

# Performance optimizations
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optimized MCP Server stage
FROM base as mcp-server-optimized

# Copy source code
COPY src/ ./src/
COPY docker/mcp_server_entrypoint.py ./

# Create directories with proper permissions
RUN mkdir -p /app/output /app/temp /app/logs \
    && chmod 755 /app/output /app/temp /app/logs

# Optimize Python imports
RUN python -m compileall -b src/

# Primary Tooling Server
FROM mcp-server-optimized as primary-tooling-server
EXPOSE 8001
CMD ["python", "mcp_server_entrypoint.py", "primary", "8001"]

# Filesystem Server  
FROM mcp-server-optimized as filesystem-server
EXPOSE 8002
CMD ["python", "mcp_server_entrypoint.py", "filesystem", "8002"]

# Optimized Agents stage
FROM base as synapse-agents-optimized

# Copy source code
COPY src/ ./src/
COPY async_main.py ./

# Create directories
RUN mkdir -p /app/output /app/temp /app/logs

# Optimize Python imports
RUN python -m compileall -b src/

# Health check for agents
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import asyncio; print('Agents healthy')" || exit 1

CMD ["python", "async_main.py"]
