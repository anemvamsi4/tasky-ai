# Use Python 3.12 slim base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY api_server/ api_server/
COPY tasky_agent/ tasky_agent/
COPY main.py ./

# Set environment variables
ENV PORT=8080

# Run the application
ENTRYPOINT ["sh", "-c"]
CMD ["uvicorn main:app --host 0.0.0.0 --port $PORT"]