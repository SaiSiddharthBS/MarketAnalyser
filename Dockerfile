FROM python:3.10-slim

# Set timezone to IST for accurate cron scheduling
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY backend/ .

# Ensure data directory exists for SQLite
RUN mkdir -p /app/data

# Run the scheduler
ENV PYTHONPATH=/app
CMD ["python", "scheduler.py"]
