# Dockerfile for Flask monitoring application

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_monitoring.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_monitoring.txt

# Copy application
COPY monitoring.py .
COPY monitoring_example.py .

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["python", "-u", "monitoring_example.py"]
