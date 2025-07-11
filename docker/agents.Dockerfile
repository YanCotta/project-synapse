# Dockerfile for Synapse Agents
FROM python:3.11-slim

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
COPY async_main.py ./

# Create necessary directories
RUN mkdir -p /app/output /app/temp /app/logs

# Set Python path
ENV PYTHONPATH=/app

# Run the agent application
CMD ["python", "async_main.py"]
