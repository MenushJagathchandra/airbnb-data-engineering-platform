FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies for potential package compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy directories
COPY config/ ./config/
COPY src/ ./src/
COPY tests/ ./tests/

# Set up storage directories
RUN mkdir -p data/raw data/cleaned data/gold

# Default execution runs the ETL and Analytics pipeline
CMD ["python", "src/main.py"]
