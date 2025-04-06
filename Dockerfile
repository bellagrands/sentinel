FROM python:3.11-slim

LABEL maintainer="Sentinel Project Team"
LABEL description="Sentinel Democracy Watchdog System"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=interface/dashboard/__init__.py
ENV FLASK_ENV=development
ENV PYTHONPATH=/app

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]