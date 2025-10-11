FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create data directory for guild config
RUN mkdir -p /app/data

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the bot
CMD ["python", "main.py"]
